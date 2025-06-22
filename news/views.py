from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import Post, Category, CarouselSlide, NewsletterSubscriber, PostView
from .forms import CustomUserCreationForm, LoginForm, PostForm, CategoryForm, CarouselSlideForm
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image
import io
from django.core.files.base import ContentFile
from django.db.models import Max, Sum, Q
from cloudinary.exceptions import BadRequest
from django.db import IntegrityError

def global_context(request):
    return {
        'categories': Category.objects.all(),
        'current_year': datetime.now().year,
    }

def generate_unique_slug(title, model_class, instance=None):
    """Generate a unique slug by appending a number if needed."""
    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    while model_class.objects.filter(slug=slug).exclude(pk=instance.pk if instance else None).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug

def home(request):
    posts = Post.objects.select_related('category', 'author').filter(status=Post.PostStatus.PUBLISHED)
    carousel_slides = CarouselSlide.get_active_slides()[:3]
    trending_posts = Post.get_trending_posts(limit=3)
    categories = Category.objects.all()
    paginator = Paginator(posts, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'posts': page_obj,
        'carousel_slides': carousel_slides,
        'trending_posts': trending_posts,
        'categories': categories,
        'current_year': datetime.now().year,
    }
    return render(request, 'home.html', context)

def search(request):
    query = request.GET.get('q', '')
    posts = Post.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query) | Q(excerpt__icontains=query),
        status=Post.PostStatus.PUBLISHED
    ).select_related('category', 'author') if query else Post.objects.filter(
        status=Post.PostStatus.PUBLISHED
    ).select_related('category', 'author')
    categories = Category.objects.all()
    carousel_slides = CarouselSlide.get_active_slides()[:5]
    paginator = Paginator(posts, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'home.html', {
        'posts': page_obj,
        'query': query,
        'categories': categories,
        'carousel_slides': carousel_slides,
        'current_year': datetime.now().year,
    })

def category_filter(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(
        category=category, status=Post.PostStatus.PUBLISHED
    ).select_related('category', 'author')
    categories = Category.objects.all()
    carousel_slides = CarouselSlide.get_active_slides()[:5]
    paginator = Paginator(posts, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'home.html', {
        'posts': page_obj,
        'category': category,
        'categories': categories,
        'carousel_slides': carousel_slides,
        'current_year': datetime.now().year,
    })

def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.select_related('category', 'author').prefetch_related('tags'),
        slug=slug, status=Post.PostStatus.PUBLISHED
    )
    post.increment_views()
    categories = Category.objects.all()
    related_posts = Post.objects.filter(
        category=post.category, status=Post.PostStatus.PUBLISHED
    ).exclude(pk=post.pk).select_related('category')[:3]
    return render(request, 'post_detail.html', {
        'post': post,
        'categories': categories,
        'related_posts': related_posts,
        'current_year': datetime.now().year,
    })

def newsletter_subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
            if created or not subscriber.is_active:
                subscriber.is_active = True
                subscriber.unsubscribed_at = None
                subscriber.save()
                messages.success(request, 'Subscribed successfully!')
            else:
                messages.info(request, 'You are already subscribed.')
        else:
            messages.error(request, 'Please provide a valid email.')
    return redirect('news:home')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to RealNaijaGist.')
            return redirect('news:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {
        'form': form,
        'current_year': datetime.now().year
    })

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'news:home')
                messages.success(request, f'Welcome back {username}')
                print("it worked")
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {
        'form': form,
        'current_year': datetime.now().year
    })

def about(request):
    return render(request, 'about.html', {'current_year': datetime.now().year})

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        if name and email and message:
            send_mail(
                subject=f'Contact Form Submission from {name}',
                message=f'From: {name}\nEmail: {email}\n\n{message}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('news:contact')
        else:
            messages.error(request, 'Please fill out all fields.')
    return render(request, 'contact.html', {'current_year': datetime.now().year})

def privacy(request):
    return render(request, 'privacy.html', {'current_year': datetime.now().year})

def terms(request):
    return render(request, 'terms.html', {'current_year': datetime.now().year})

def advertise(request):
    return render(request, 'advertise.html', {'current_year': datetime.now().year})

def write(request):
    return render(request, 'write.html', {'current_year': datetime.now().year})

def is_staff(user):
    return user.is_staff or user.is_superuser

def is_admin(user):
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_staff)
def post_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    posts = Post.objects.select_related('category', 'author').all()
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))
    if category_id:
        posts = posts.filter(category_id=category_id)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    categories = Category.objects.all()
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'current_year': datetime.now().year,
    }
    return render(request, 'post_list.html', context)

@login_required
@user_passes_test(is_staff)
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        try:
            featured_image = request.FILES.get('featured_image')
            if featured_image and featured_image.size > 10 * 1024 * 1024:
                form.add_error(
                    'featured_image',
                    f"File size too large. Please reduce to less than 10 MB. "
                    f"Uploaded file is {featured_image.size / (1024 * 1024):.2f} MB."
                )
            if form.is_valid():
                post = form.save(commit=False)
                post.author = request.user
                post.slug = generate_unique_slug(post.title, Post)
                post.excerpt = post.content[:150] if post.content else ''
                post.meta_description = post.excerpt or post.content[:160]
                post.image_alt_text = post.title
                if post.featured_image:
                    img = Image.open(post.featured_image)
                    webp_io = io.BytesIO()
                    img.save(webp_io, format='WEBP', quality=80)
                    post.featured_image_webp.save(
                        f"{post.featured_image.name.rsplit('.', 1)[0]}.webp",
                        ContentFile(webp_io.getvalue()),
                        save=False
                    )
                post.cdn_image_url = ''
                post.save()
                form.save_m2m()
                post.meta_keywords = ', '.join([tag.name for tag in post.tags.all()] + [post.category.name]) if post.tags.exists() else post.category.name
                post.save()
                messages.success(request, 'Post created successfully!')
                if request.headers.get('HX-Request'):
                    context = {
                        'section': 'posts',
                        'posts': Post.objects.all().order_by('-created_at')[:10],
                        'categories': Category.objects.all(),
                        'query': request.GET.get('q', ''),
                        'selected_category': request.GET.get('category', ''),
                    }
                    return render(request, 'admin_dashboard.html', context, headers={'HX-Trigger': 'reloadContent'})
                return redirect('news:admin_dashboard')
            else:
                if request.headers.get('HX-Request'):
                    context = {'form': form}
                    return render(request, 'partials/post_form.html', context)
                messages.error(request, 'Please correct the errors below.')
        except BadRequest as e:
            form.add_error(
                'featured_image',
                f"Cloudinary error: {str(e)}. Please ensure the file is less than 10 MB."
            )
            if request.headers.get('HX-Request'):
                context = {'form': form}
                return render(request, 'partials/post_form.html', context)
            messages.error(request, 'Please correct the errors below.')
        except IntegrityError as e:
            form.add_error(
                'title',
                'A post with a similar title already exists. Please modify the title to make it unique.'
            )
            if request.headers.get('HX-Request'):
                context = {'form': form}
                return render(request, 'partials/post_form.html', context)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PostForm()
    
    context = {
        'form': form,
        'current_year': datetime.now().year,
    }
    template = 'partials/post_form.html' if request.headers.get('HX-Request') else 'post_form.html'
    return render(request, template, context)

@login_required
@user_passes_test(is_staff)
def post_update(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        try:
            featured_image = request.FILES.get('featured_image')
            if featured_image and featured_image.size > 10 * 1024 * 1024:
                form.add_error(
                    'featured_image',
                    f"File size too large. Please reduce to less than 10 MB. "
                    f"Uploaded file is {featured_image.size / (1024 * 1024):.2f} MB."
                )
            if form.is_valid():
                updated_post = form.save(commit=False)
                updated_post.slug = generate_unique_slug(updated_post.title, Post, instance=post)
                updated_post.excerpt = updated_post.content[:150] if updated_post.content else ''
                updated_post.meta_description = updated_post.excerpt or updated_post.content[:160]
                updated_post.image_alt_text = updated_post.title
                if updated_post.featured_image:
                    img = Image.open(updated_post.featured_image)
                    webp_io = io.BytesIO()
                    img.save(webp_io, format='WEBP', quality=80)
                    updated_post.featured_image_webp.save(
                        f"{updated_post.featured_image.name.rsplit('.', 1)[0]}.webp",
                        ContentFile(webp_io.getvalue()),
                        save=False
                    )
                updated_post.cdn_image_url = ''
                updated_post.save()
                form.save_m2m()
                updated_post.meta_keywords = ', '.join([tag.name for tag in updated_post.tags.all()] + [updated_post.category.name]) if updated_post.tags.exists() else updated_post.category.name
                updated_post.save()
                messages.success(request, 'Post updated successfully!')
                if request.headers.get('HX-Request'):
                    context = {
                        'section': 'posts',
                        'posts': Post.objects.all().order_by('-created_at')[:10],
                        'categories': Category.objects.all(),
                        'query': request.GET.get('q', ''),
                        'selected_category': request.GET.get('category', ''),
                    }
                    return render(request, 'admin_dashboard.html', context, headers={'HX-Trigger': 'reloadContent'})
                return redirect('news:admin_dashboard')
            else:
                if request.headers.get('HX-Request'):
                    context = {'form': form, 'post': post}
                    return render(request, 'partials/post_form.html', context)
                messages.error(request, 'Please correct the errors below.')
        except BadRequest as e:
            form.add_error(
                'featured_image',
                f"Cloudinary error: {str(e)}. Please ensure the file is less than 10 MB."
            )
            if request.headers.get('HX-Request'):
                context = {'form': form, 'post': post}
                return render(request, 'partials/post_form.html', context)
            messages.error(request, 'Please correct the errors below.')
        except IntegrityError as e:
            form.add_error(
                'title',
                'A post with a similar title already exists. Please modify the title to make it unique.'
            )
            if request.headers.get('HX-Request'):
                context = {'form': form, 'post': post}
                return render(request, 'partials/post_form.html', context)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PostForm(instance=post)
    
    context = {
        'form': form,
        'post': post,  # Ensure post is passed for form action
        'current_year': datetime.now().year,
    }
    template = 'partials/post_form.html' if request.headers.get('HX-Request') else 'post_form.html'
    return render(request, template, context)

@login_required
@user_passes_test(is_staff)
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        if request.headers.get('HX-Request'):
            context = {
                'section': 'posts',
                'posts': Post.objects.all().order_by('-created_at')[:10],
                'categories': Category.objects.all(),
                'query': request.GET.get('q', ''),
                'selected_category': request.GET.get('category', ''),
            }
            return render(request, 'admin_dashboard.html', context, headers={'HX-Trigger': 'reloadContent'})
        return redirect('news:admin_dashboard')
    context = {
        'post': post,
        'current_year': datetime.now().year,
    }
    return render(request, 'post_confirm_delete.html', context)

@login_required
@user_passes_test(is_staff)
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.slug = generate_unique_slug(category.name, Category)
            category.save()
            messages.success(request, 'Category added successfully.')
            if request.headers.get('HX-Request'):
                context = {
                    'section': 'categories',
                    'page_obj': Paginator(Category.objects.order_by('name'), 10).get_page(request.GET.get('page')),
                    'categories': Category.objects.all(),
                }
                return render(request, 'admin_dashboard.html', context, headers={'HX-Trigger': 'reloadContent'})
            return redirect(reverse('news:admin_dashboard') + '?section=categories')
        else:
            if request.headers.get('HX-Request'):
                return render(request, 'partials/category_form.html', {'form': form})
            messages.error(request, 'Please correct the errors below.')
    form = CategoryForm()
    return render(request, 'partials/category_form.html', {'form': form})

@login_required
@user_passes_test(is_staff)
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save(commit=False)
            category.slug = generate_unique_slug(category.name, Category, instance=category)
            category.save()
            messages.success(request, 'Category updated successfully.')
            if request.headers.get('HX-Request'):
                context = {
                    'section': 'categories',
                    'page_obj': Paginator(Category.objects.order_by('name'), 10).get_page(request.GET.get('page')),
                    'categories': Category.objects.all(),
                }
                return render(request, 'admin_dashboard.html', context, headers={'HX-Trigger': 'reloadContent'})
            return redirect(reverse('news:admin_dashboard') + '?section=categories')
        else:
            if request.headers.get('HX-Request'):
                return render(request, 'partials/category_form.html', {'form': form, 'category': category})
            messages.error(request, 'Please correct the errors below.')
    form = CategoryForm(instance=category)
    return render(request, 'partials/category_form.html', {'form': form, 'category': category})

@login_required
@user_passes_test(is_staff)
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
        if request.headers.get('HX-Request'):
            context = {
                'section': 'categories',
                'page_obj': Paginator(Category.objects.order_by('name'), 10).get_page(request.GET.get('page')),
                'categories': Category.objects.all(),
            }
            return render(request, 'admin_dashboard.html', context, headers={'HX-Trigger': 'reloadContent'})
        return redirect(reverse('news:admin_dashboard') + '?section=categories')
    return render(request, '404.html', status=405)

@login_required
@user_passes_test(is_staff)
def add_carousel_slide(request):
    if request.method == 'POST':
        form = CarouselSlideForm(request.POST, request.FILES)
        if form.is_valid():
            slide = form.save(commit=False)
            max_order = CarouselSlide.objects.aggregate(Max('order'))['order__max']
            slide.order = (max_order + 1) if max_order is not None else 0
            if slide.image:
                img = Image.open(slide.image)
                webp_io = io.BytesIO()
                img.save(webp_io, format='WEBP', quality=80)
                slide.image_webp.save(
                    f"{slide.image.name.rsplit('.', 1)[0]}.webp",
                    ContentFile(webp_io.getvalue()),
                    save=False
                )
            slide.save()
            messages.success(request, 'Carousel slide added successfully.')
            if request.headers.get('HX-Request'):
                context = {
                    'section': 'carousel',
                    'page_obj': Paginator(CarouselSlide.objects.order_by('-id'), 10).get_page(request.GET.get('page')),
                    'categories': Category.objects.all(),
                }
                return render(request, 'admin_dashboard.html', context, headers={'HX-Trigger': 'reloadContent'})
            return redirect(reverse('news:admin_dashboard') + '?section=carousel')
        else:
            if request.headers.get('HX-Request'):
                return render(request, 'partials/carousel_slide_form.html', {'form': form})
            messages.error(request, 'Please correct the errors below.')
    form = CarouselSlideForm()
    return render(request, 'partials/carousel_slide_form.html', {'form': form})

@login_required
@user_passes_test(is_staff)
def edit_carousel_slide(request, pk):
    slide = get_object_or_404(CarouselSlide, pk=pk)
    if request.method == 'POST':
        form = CarouselSlideForm(request.POST, request.FILES, instance=slide)
        if form.is_valid():
            slide = form.save(commit=False)
            if slide.image:
                img = Image.open(slide.image)
                webp_io = io.BytesIO()
                img.save(webp_io, format='WEBP', quality=80)
                slide.image_webp.save(
                    f"{slide.image.name.rsplit('.', 1)[0]}.webp",
                    ContentFile(webp_io.getvalue()),
                    save=False
                )
            slide.save()
            messages.success(request, 'Carousel slide updated successfully.')
            if request.headers.get('HX-Request'):
                context = {
                    'section': 'carousel',
                    'page_obj': Paginator(CarouselSlide.objects.order_by('-id'), 10).get_page(request.GET.get('page')),
                    'categories': Category.objects.all(),
                }
                return render(request, 'admin_dashboard.html', context, headers={'HX-Trigger': 'reloadContent'})
            return redirect(reverse('news:admin_dashboard') + '?section=carousel')
        else:
            if request.headers.get('HX-Request'):
                return render(request, 'partials/carousel_slide_form.html', {'form': form, 'slide': slide})
            messages.error(request, 'Please correct the errors below.')
    form = CarouselSlideForm(instance=slide)
    return render(request, 'partials/carousel_slide_form.html', {'form': form, 'slide': slide})

@login_required
@user_passes_test(is_staff)
def delete_carousel_slide(request, pk):
    slide = get_object_or_404(CarouselSlide, pk=pk)
    if request.method == 'POST':
        slide.delete()
        messages.success(request, 'Carousel slide deleted successfully.')
        if request.headers.get('HX-Request'):
            context = {
                'section': 'carousel',
                'page_obj': Paginator(CarouselSlide.objects.order_by('-id'), 10).get_page(request.GET.get('page')),
                'categories': Category.objects.all(),
            }
            return render(request, 'admin_dashboard.html', context, headers={'HX-Trigger': 'reloadContent'})
        return redirect(reverse('news:admin_dashboard') + '?section=carousel')
    return render(request, '404.html', status=405)

@login_required
@user_passes_test(is_staff)
def delete_subscriber(request, pk):
    subscriber = get_object_or_404(NewsletterSubscriber, pk=pk)
    if request.method == 'POST':
        subscriber.delete()
        messages.success(request, 'Subscriber removed successfully.')
        if request.headers.get('HX-Request'):
            context = {
                'section': 'subscribers',
                'page_obj': Paginator(NewsletterSubscriber.objects.order_by('-subscribed_at'), 10).get_page(request.GET.get('page')),
                'categories': Category.objects.all(),
            }
            return render(request, 'admin_dashboard.html', context, headers={'HX-Trigger': 'reloadContent'})
        return redirect(reverse('news:admin_dashboard') + '?section=subscribers')
    return render(request, '404.html', status=405)

# Duplicate admin views removed (add_post, edit_post, delete_post)
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    section = request.GET.get('section', 'posts')
    query = request.GET.get('q', '')
    category_filter = request.GET.get('category', '')
    
    # Calculate stats for dashboard
    last_month = timezone.now() - timedelta(days=30)
    total_posts = Post.objects.count()
    post_growth = Post.objects.filter(created_at__gte=last_month).count() / (total_posts or 1) * 100
    active_categories = Category.objects.count()
    new_categories = Category.objects.filter(created_at__gte=last_month).count()
    subscribers = NewsletterSubscriber.objects.filter(is_active=True).count()
    subscriber_growth = NewsletterSubscriber.objects.filter(subscribed_at__gte=last_month, is_active=True).count() / (subscribers or 1) * 100
    monthly_views = PostView.objects.filter(viewed_at__gte=last_month).aggregate(total=Sum('post__views'))['total'] or 0
    previous_month_views = PostView.objects.filter(viewed_at__lt=last_month, viewed_at__gte=timezone.now() - timedelta(days=60)).aggregate(total=Sum('post__views'))['total'] or 1
    view_change = ((monthly_views - previous_month_views) / previous_month_views) * 100

    context = {
        'user': request.user,
        'section': section,
        'query': query,
        'category_filter': category_filter,
        'categories': Category.objects.all(),
        'current_year': datetime.now().year,
        'stats': {
            'total_posts': total_posts,
            'post_growth': round(post_growth, 1),
            'active_categories': active_categories,
            'new_categories': new_categories,
            'subscribers': subscribers,
            'subscriber_growth': round(subscriber_growth, 1),
            'monthly_views': monthly_views,
            'view_change': round(view_change, 1),
        },
    }

    if section == 'posts':
        posts = Post.objects.select_related('category', 'author').order_by('-created_at')
        if query:
            posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))
        if category_filter:
            posts = posts.filter(category__name=category_filter)
        paginator = Paginator(posts, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
        context['page_obj'] = page_obj
    elif section == 'categories':
        categories = Category.objects.order_by('name')
        paginator = Paginator(categories, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
        context['page_obj'] = page_obj
    elif section == 'carousel':
        slides = CarouselSlide.objects.order_by('-id')
        paginator = Paginator(slides, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
        context['page_obj'] = page_obj
    elif section == 'subscribers':
        subscribers = NewsletterSubscriber.objects.order_by('-subscribed_at')
        paginator = Paginator(subscribers, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
        context['page_obj'] = page_obj

    return render(request, 'admin_dashboard.html', context)
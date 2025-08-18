from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Post, Category, CarouselSlide, Comment, Like
from taggit.forms import TagWidget
import os

    
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'newsletter-input',
            'placeholder': 'Enter your email'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'newsletter-input',
            'placeholder': 'Enter your username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'newsletter-input',
            'placeholder': 'Enter your password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'newsletter-input',
            'placeholder': 'Confirm your password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
    
class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'newsletter-input',
            'placeholder': 'Enter your username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'newsletter-input',
            'placeholder': 'Enter your password'
        })
    )


class PostForm(forms.ModelForm):
    featured_image = forms.FileField(
        help_text="Maximum file size is 10MB. Supported formats: JPEG, PNG.",
        widget=forms.FileInput(attrs={'class': 'form-group'}),
        required=False
    )
    
    featured_video = forms.FileField(
        help_text="Maximum file size is 100MB. Supported formats: MP4, WebM, MOV.",
        widget=forms.FileInput(attrs={'class': 'form-group'}),
        required=False
    )
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'status', 'category', 'tags', 'featured_image', 'featured_video', 'video_embed_url', 'is_video_post', 'is_trending']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'ck-editor__editable'}),
            'tags': TagWidget(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-group'}),
            'category': forms.Select(attrs={'class': 'form-group'}),
            'is_trending': forms.CheckboxInput(attrs={'class': 'form-group'}),
            'is_video_post': forms.CheckboxInput(attrs={'class': 'form-group'}),
            'featured_image': forms.FileInput(attrs={'class': 'form-group'}),
            'featured_video': forms.FileInput(attrs={'class': 'form-group'}),
            'video_embed_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.youtube.com/embed/...'}),
        }
        help_texts = {
            'featured_image': 'Maximum file size is 10MB. Supported formats: JPEG, PNG.',
            'featured_video': 'Maximum file size is 100MB. Supported formats: MP4, WebM, MOV.',
            'video_embed_url': 'YouTube or Vimeo embed URL for external videos.',
            'is_video_post': 'Mark if this post is primarily a video post.',
        }
        def clean_featured_image(self):
            featured_image = self.cleaned_data.get('featured_image')
            if featured_image:
                # Check file size (10 MB = 10,485,760 bytes)
                max_size = 10 * 1024 * 1024  # 10 MB
                if featured_image.size > max_size:
                    raise forms.ValidationError(
                        f"File size too large. Maximum is {max_size / (1024 * 1024)} MB. "
                        f"Uploaded file is {featured_image.size / (1024 * 1024):.2f} MB."
                    )
            return featured_image
        
        def clean_featured_video(self):
            featured_video = self.cleaned_data.get('featured_video')
            if featured_video:
                # Check file size (100 MB = 104,857,600 bytes)
                max_size = 100 * 1024 * 1024  # 100 MB
                if featured_video.size > max_size:
                    raise forms.ValidationError(
                        f"Video file size too large. Maximum is {max_size / (1024 * 1024)} MB. "
                        f"Uploaded file is {featured_video.size / (1024 * 1024):.2f} MB."
                    )
                
                # Check file extension
                allowed_extensions = ['.mp4', '.webm', '.mov', '.avi', '.mkv']
                file_extension = os.path.splitext(featured_video.name)[1].lower()
                if file_extension not in allowed_extensions:
                    raise forms.ValidationError(
                        f"Unsupported video format. Allowed formats: {', '.join(allowed_extensions)}"
                    )
            return featured_video
        
        def clean(self):
            cleaned_data = super().clean()
            # Ensure file size is checked even if CloudinaryField bypasses clean_featured_image
            featured_image = self.files.get('featured_image')
            if featured_image:
                max_size = 10 * 1024 * 1024
                if featured_image.size > max_size:
                    self.add_error(
                        'featured_image',
                        f"File size too large. Please reduce to less than 10 MB. "
                        f"Uploaded file is {featured_image.size / (1024 * 1024):.2f} MB."
                    )
            return cleaned_data

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-group'}),
            'name': forms.TextInput(attrs={'class': 'form-group'}),
        }

class CarouselSlideForm(forms.ModelForm):
    class Meta:
        model = CarouselSlide
        fields = ['title', 'description', 'image', 'is_active', 'featured_until']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-group'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-group'}),
            'image': forms.FileInput(attrs={'class': 'form-group'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-group'}),
            'featured_until': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-group'}),
        }
        help_texts = {
            'image': 'Maximum file size is 10MB. Supported formats: JPEG, PNG.',
        }
        
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'comment-input',
                'placeholder': 'Write your comment...',
                'rows': 4,
            }),
        }
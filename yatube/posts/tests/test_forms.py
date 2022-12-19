import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')
        Post.objects.create(
            text='Тестовый текст поста',
            author=cls.author,
            group=Group.objects.create(title='Тестовое имя группы',
                                       slug='test_slug',
                                       description='Тестовая группа')
        )
        Group.objects.create(title='Имя второй тестовой группы',
                             slug='second_test_slug',
                             description='Вторая тестовая группа')
        Comment.objects.create(
            post=Post.objects.get(text='Тестовый текст поста'),
            author=cls.author,
            text='Первый комментарий к первому посту'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post_in_database(self):
        """При отправке валидной формы создания поста
            создается новая запись в базе данных"""
        posts_count = Post.objects.count()
        group_id = Group.objects.get(slug='test_slug').id
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Создаваемый пост',
            'group': group_id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                             args=['TestAuthor']))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Создаваемый пост',
                group=group_id,
                author=self.author,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post_in_database(self):
        """При отправке валидной формы редактирования поста происходит
           изменение поста с тем-же post_id в базе данных"""
        posts_count = Post.objects.count()
        second_group_id = Group.objects.get(slug='second_test_slug').id
        post_id = Post.objects.get(text='Тестовый текст поста').id
        form_data = {
            'text': 'Измененный текст поста',
            'group': second_group_id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[post_id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             args=[post_id]))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Измененный текст поста',
                group=second_group_id,
                author=self.author,
            ).exists()
        )

    def test_comment_post_in_database(self):
        """При отправке валидной формы coздания комментария
            создается новая запись в базе данных"""
        comment_count = Comment.objects.count()
        post_id = Post.objects.get(text='Тестовый текст поста').id
        form_data = {
            'text': 'Второй комментарий первого поста'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[post_id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             args=[post_id]))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Второй комментарий первого поста',
                post=post_id,
                author=self.author
            ).exists()
        )

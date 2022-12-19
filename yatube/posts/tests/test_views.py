import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.core.cache import cache
from ..models import Group, Post, User, Follow
from django.urls import reverse
from django import forms
import time
from yatube.settings import POSTS_NUMBER

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.first_author = User.objects.create_user(username='TestAuthorOne')
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.first_author,
            group=Group.objects.create(title='Тестовое имя группы',
                                       slug='test_slug',
                                       description='Тестовая группа')
        )
        time.sleep(0.01)

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

        second_author = User.objects.create_user(username='TestAuthorTwo')
        cls.second_post = Post.objects.create(
            text='Текст второго поста',
            author=second_author,
            group=Group.objects.create(title='Тестовое имя второй группы',
                                       slug='test_slug_two',
                                       description='Вторая тестовая группа'),
            image=uploaded
        )

        cls.post_obj = [
            cls.second_post,
            cls.post
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author = User.objects.get(username='TestAuthorOne')
        self.first_author_client = Client()
        self.first_author_client.force_login(self.author)
        self.post_id = Post.objects.get(author=self.author).id

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'TestAuthorOne'}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post_id}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post_id}):
                'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.first_author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.first_author_client.get(reverse('posts:index'))
        context_object = list(response.context['page_obj'])
        self.assertEqual(context_object, list(self.post_obj))
        self.assertEqual(context_object[0].image, 'posts/small.gif',
                         'Картинка не соответствует или отсутствует')
        self.assertFalse(context_object[1].image, 'Поле image не пустое')

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.first_author_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test_slug_two'})
        )
        context_object = response.context['page_obj'][0]
        context = self.post_obj[0]
        self.assertEqual(context_object, context)
        self.assertEqual(context_object.image, 'posts/small.gif',
                         'Картинка не соответствует или отсутствует')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.first_author_client.get(reverse('posts:profile',
                                                kwargs={'username':
                                                        'TestAuthorTwo'}))
        context_object = response.context['page_obj'][0]
        context = self.post_obj[0]
        self.assertEqual(context_object, context)
        self.assertEqual(context_object.image, 'posts/small.gif',
                         'Картинка не соответствует или отсутствует')

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.first_author_client.get(reverse('posts:post_detail',
                                                kwargs={'post_id': 2}))
        context_object = response.context['post']
        context_count = response.context['post_count']
        self.assertEqual(context_object, self.post_obj[0])
        self.assertEqual(context_count, 1)
        self.assertEqual(context_object.image, 'posts/small.gif',
                         'Картинка не соответствует или отсутствует')

    def test_add_comment_view_add_comments_to_post_detail(self):
        """Функция add_comment добавляет комментарий к посту
            с правильным контекстом"""
        post_id = Post.objects.get(text='Текст второго поста').id
        form_data = {
            'text': 'Комментарий к второму посту'
        }
        self.first_author_client.post(
            reverse('posts:add_comment', args=[post_id]),
            data=form_data,
        )
        response = self.first_author_client.get(reverse('posts:post_detail',
                                                kwargs={'post_id': post_id}))
        context_object = response.context['comments'][0]
        self.assertEqual(context_object.text, 'Комментарий к второму посту',
                         'Текст комментария неверный')
        self.assertEqual(context_object.author, self.first_author,
                         'не соответствует автор комментария')

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом"""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        def comparison(response):
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

        response_edit = self.first_author_client.get(reverse('posts:post_edit',
                                                     kwargs={'post_id': 1}))
        response_create = (self.first_author_client
                           .get(reverse('posts:post_create')))
        comparison(response_edit)
        comparison(response_create)

    def test_cache_index_page_show_correct_context(self):
        """В шаблоне index кешируется контент"""
        response = self.first_author_client.get(reverse('posts:index'))
        initial_content = response.content
        Post.objects.create(
            text='Пост для проверки кэширования',
            author=self.author,
        )
        response = self.first_author_client.get(reverse('posts:index'))
        cached_content = response.content
        self.assertEqual(initial_content, cached_content)
        cache.clear()
        response = self.first_author_client.get(reverse('posts:index'))
        new_content = response.content
        self.assertNotEqual(initial_content, new_content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        author = User.objects.create_user(username='TestAuthor')
        group = Group.objects.create(title='Тестовое имя группы',
                                     slug='test_slug',
                                     description='Тестовая группа')

        cls.templates_pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}),
            reverse('posts:profile', kwargs={'username': 'TestAuthor'})
        ]

        posts_list = []
        for i in range(POSTS_NUMBER + 3):
            posts_list.append(
                Post
                (text='Тестовый текст поста ' + str(i),
                 author=author,
                 group=group,
                 )
            )
        Post.objects.bulk_create(posts_list)

    def setUp(self):
        self.guest_client = Client()

    def test_first_pages_contains_ten_records(self):
        """Первые страницы index, group_list, profile содержат
            количество постов, заданное в POSTS_NUMBER"""
        for reverse_name in self.templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']),
                                 POSTS_NUMBER)

    def test_second_pages_contains_three_records(self):
        """Вторые страницы index, group_list, profile содержат по 3 поста"""
        for reverse_name in self.templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)


class FollowPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.first_user = User.objects.create_user(username='TestUserOne')
        cls.second_user = User.objects.create_user(username='TestUserTwo')
        cls.author = User.objects.create_user(username='TestAuthor')
        Follow.objects.create(
            user=cls.second_user,
            author=cls.author
        )
        cls.follow_count = Follow.objects.count()

    def setUp(self):
        self.first_user_client = Client()
        self.second_user_client = Client()
        self.author_client = Client()
        self.first_user_client.force_login(self.first_user)
        self.second_user_client.force_login(self.second_user)
        self.author_client.force_login(self.author)

    def test_authorized_user_can_follow(self):
        """При подписке авторизованного пользователя на другого
        автора создается запись в базе данных"""
        response = self.first_user_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'TestAuthor'}))
        self.assertTrue(
            Follow.objects.filter(
                user=self.first_user,
                author=self.author,
            ).exists(), 'Не добавилась запись о подписке в БД'
        )
        self.assertEqual(Follow.objects.count(), self.follow_count + 1)
        self.assertRedirects(response, reverse('posts:profile',
                             args=['TestAuthor']))

    def test_authorized_user_can_unfollow(self):
        """При отписке авторизованного пользователя от другого
        автора удаляется запись в базе данных"""
        response = self.second_user_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': 'TestAuthor'}))
        self.assertFalse(
            Follow.objects.filter(
                user=self.second_user,
                author=self.author,
            ).exists(), 'Не удалилась запись о подписке в БД'
        )
        self.assertEqual(Follow.objects.count(), self.follow_count - 1)
        self.assertRedirects(response, reverse('posts:profile',
                             args=['TestAuthor']))

    def test_follow_page_use_correct_context(self):
        """Посты автора появляются в шаблоне follow_index
            только у подписчиков автора"""
        self.post = Post.objects.create(
            text='Тестовый текст поста',
            author=self.author,
        )
        not_follower_response = self.first_user_client.get(
            reverse('posts:follow_index'))
        follower_response = self.second_user_client.get(
            reverse('posts:follow_index'))
        context = self.post
        follower_context_object = follower_response.context['page_obj']
        self.assertIn(context, follower_context_object,
                      'Пост не отобразился у подписчика')
        not_follower_context_object = not_follower_response.context['page_obj']
        self.assertNotIn(context, not_follower_context_object,
                         'Пост отобразился у неподписанного пользователя')

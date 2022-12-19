from django.test import TestCase, Client
from posts.models import Post, Group
from ..models import User
from http import HTTPStatus


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        post_author = User.objects.create_user(username='TestAuthor')
        Post.objects.create(
            text='Тестовый текст поста',
            author=post_author,
            group=Group.objects.create(title='Тестовое имя группы',
                                       slug='test_slug',
                                       description='Тестовая группа')
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.author = User.objects.get(username='TestAuthor')
        self.authorized_client = Client()
        self.post_author_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author_client.force_login(self.author)

    def test_pages_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        adresses = ['/', '/group/test_slug/', '/profile/TestUser/',
                    '/posts/1/']
        for adress in adresses:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_exists_page(self):
        """Запрос к несуществующей странице выдает ошибку 404"""
        response = self.guest_client.get('/unexisting_page/', follow=True)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_exists_at_desired_location(self):
        """Страница /posts/<post_id>/edit/ доступна автору поста"""
        response = self.post_author_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_not_author_on_post_detail(self):
        """Страница /posts/<post_id>/edit/ перенаправит любого пользователя
        кроме автора на страницу поста"""
        response = self.authorized_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(response, '/posts/1/')

    def test_create_url_redirect_anonymous_on_login(self):
        """Страница /create/ перенаправляет анонимного пользователя
        на страницу логина"""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_comment_url_redirect_anonymous_on_login(self):
        """Страница /posts/<post_id>/comment/ перенаправляет анонимного
        пользователя на страницу логина"""
        response = self.guest_client.get('/posts/1/comment/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/posts/1/comment/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/': 'posts/index.html',
            '/posts/1/': 'posts/post_detail.html',
            '/profile/TestUser/': 'posts/profile.html',
            '/unexisting_page/': 'core/404.html',
            '/follow/': 'posts/follow.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.post_author_client.get(adress)
                self.assertTemplateUsed(response, template)

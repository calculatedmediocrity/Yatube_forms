from django.test import TestCase, Client
from http import HTTPStatus

from ..models import User, Group, Post


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.creator = User.objects.create_user(
            username='test_author'
        )
        cls.authorized_creator = Client()
        cls.authorized_creator.force_login(cls.creator)
        cls.viewer = User.objects.create_user(
            username='test_not_author'
        )
        cls.authorized_viewer = Client()
        cls.authorized_viewer.force_login(cls.viewer)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.creator,
            group=cls.group,
            text='Тестовый пост',
        )

        cls.public_pages = (
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.creator.username}/',
            f'/posts/{cls.post.id}/',
        )
        cls.private_pages = (
            '/create/',
            f'/posts/{cls.post.id}/edit/',
        )

    def test_public_urls_exist_at_desired_location(self):
        """Доступ неавторизованных пользователей"""
        for url in self.public_pages:
            response = self.guest_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_urls_exist_at_desired_location(self):
        """Доступ авторизованных пользователей"""
        for url in self.private_pages:
            response = self.authorized_creator.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_url_returns_404(self):
        """Несуществующая страница возвращает 404 статус-код"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_url_redirects_anonymous(self):
        """Перенаправление неавторизованного пользователя со страницы create."""
        response = self.guest_client.get(self.private_pages[0], follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_url_redirects_anonymous(self):
        """Перенаправление неавторизованного пользователя со страницы edit."""
        response = self.guest_client.get(self.private_pages[0], follow=True)
        self.assertRedirects(response, f'/auth/login/?next=/create/')

    def test_edit_url_redirects_authorised(self):
        """Перенаправление авторизованного пользователя без прав со страницы edit."""
        response = self.authorized_viewer.get(self.private_pages[1], follow=True)
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.creator}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_creator.get(url)
                self.assertTemplateUsed(response, template)

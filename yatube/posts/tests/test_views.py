from django.test import TestCase, Client
from django.urls import reverse
from django import forms

from ..models import User, Group, Post


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.creator = User.objects.create_user(
            username='creator_name'
        )
        cls.authorized_creator = Client()
        cls.authorized_creator.force_login(cls.creator)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание',
        )

        cls.second_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-group2',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.creator,
            text='Тестовый пост',
            group=cls.group,
        )

    def check_post_fields(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.group.id, self.post.group.id)

    def test_pages_uses_correct_template(self):
        """View-классы используют ожидаемые HTML-шаблоны."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', args=(self.group.slug,)):
                'posts/group_list.html',
            reverse('posts:profile', args=(self.creator.username,)):
                'posts/profile.html',
            reverse('posts:post_detail', args=(self.post.pk,)):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:edit', args=(self.post.pk,)):
                'posts/create_post.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_creator.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_creator.get(reverse('posts:index'))
        self.check_post_fields(response.context['page_obj'][0])

    def test_group_list_page_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_creator.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)
        self.check_post_fields(response.context['page_obj'][0])

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_creator.get(
            reverse('posts:profile', kwargs={'username': self.post.author.username})
        )
        self.assertEqual(response.context['user_profile'], self.creator)
        self.check_post_fields(response.context['page_obj'][0])

    def test_post_detail_page_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_creator.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.check_post_fields(response.context['post'])

    def test_create_post_page_shows_correct_context(self):
        """Шаблон создания поста сформирован с правильным контекстом."""
        response = self.authorized_creator.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_page_shows_correct_context(self):
        """Шаблон редактирования поста сформирован с правильным контекстом."""
        response = self.authorized_creator.get(
            reverse('posts:edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_home_group_list_profile_pages(self):
        """Появление поста на главной странице, на странице группы,
        в профайле пользователя.
        """
        templates_url_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.post.author.username}
            ),
        )
        for url in templates_url_names:
            response = self.authorized_creator.get(url)
            self.assertEqual(len(response.context['page_obj']), 1)

    def test_post_not_in_second_group(self):
        """Пост не находится на станице другой группы"""
        response = self.authorized_creator.get(
            reverse('posts:group_list', kwargs={'slug': self.second_group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='creator_name'
        )
        cls.authorized_user = Client()
        cls.authorized_user.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание',
        )
        for i in range(13):
            Post.objects.create(
                text=f'Пост {i}',
                author=cls.user,
                group=cls.group
            )

        cls.templates_url_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
            reverse('posts:profile', kwargs={'username': cls.user}),
        ]

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

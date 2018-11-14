import shelve
from pathlib import Path

from mkdocs.config import config_options

from mkdocs.plugins import BasePlugin
from mkdocs.utils import string_types
import re


def modify_canonical_url(page, config, files):
    # 此时canonical_url 已经填充完成 需要在中间插入topic_slug
    site_url = config['site_url']
    if not site_url.endswith('/'):
        site_url += '/'
    page.canonical_url = site_url + config['topic_slug'] + '/' + page.canonical_url[len(site_url):]

    return page


def inject_topic_slug(config):
    config['topic_slug'] = config['site_dir'].split('/')[-1]
    return config


def replace_image_url(html, page, config, files):
    print(page.title)
    # relative_path = page.title
    relative_path = 'micropython-esp32'
    origin_list = re.findall(r'<img.*?src=\".*?\".*?>', html)

    html = re.sub(r'(<img.*?src=\").*?/pictures/(.*?\".*>)',
                  lambda m: m.group(1) + 'http://src.1zlab.com/' + relative_path + '/' + m.group(2), html)
    new_list = re.findall(r'<img.*?src=\".*?\".*?>', html)

    for i in range(1, len(new_list)):
        print(origin_list[i], '->', new_list[i])

    return html


def custom_env(env, config, files):
    env.trim_blocks = True
    env.lstrip_blocks = True
    return env


def pickle_context(context, page, config, nav):
    data = context
    data.pop('pages')
    data['config'] = data['config'].data
    if 'dev_addr' in data['config']:
        data['config'].pop('dev_addr')

    if data['page'].url:
        title = data['page'].url.split('/')[-2]
    else:
        title = data['config']['topic_slug']

    current_sdb_dir = Path(Path.home(), 'sdb')
    try:
        current_sdb_dir.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        print('文件夹已存在')

    with shelve.open(str(Path(current_sdb_dir, data['config']['topic_slug'] + '.sdb')), flag='c', writeback=True) as db:
        db[title] = data

    with shelve.open(str(Path(current_sdb_dir, data['config']['topic_slug'] + '.sdb')), flag='r') as db:
        data = db[title]
    return data


class EasyLabPlugin(BasePlugin):
    config_scheme = (
        ('inject_topic_slug', config_options.Type(bool, default=True)),
        ('custom_env', config_options.Type(bool, default=True)),
        ('modify_canonical_url', config_options.Type(bool, default=True)),
        ('change_image_name', config_options.Type(bool, default=False)),
        ('replace_image_url', config_options.Type(bool, default=True)),
        ('upload_qiniu', config_options.Type(bool, default=False)),
        ('pickle_context', config_options.Type(bool, default=True)),
    )

    def on_config(self, config, **kwargs):
        if self.config['inject_topic_slug']:
            config['topic_slug'] = config['site_dir'].split('/')[-1]

        return config

    def on_env(self, env, config, **kwargs):
        if self.config['custom_env']:
            env.trim_blocks = True
            env.lstrip_blocks = True
        return env

    def on_pre_page(self, page, config, **kwargs):
        if self.config['modify_canonical_url']:
            # 此时canonical_url 已经填充完成 需要在中间插入topic_slug
            site_url = config['site_url']
            if not site_url.endswith('/'):
                site_url += '/'
            page.canonical_url = site_url + config['topic_slug'] + '/' + page.canonical_url[len(site_url):]

        return page

    def on_page_content(self, content, page, **kwargs):
        # todo 自动将文件名排序
        if self.config['replace_image_url']:
            relative_path = self.config['topic_slug']
            origin_list = re.findall(r'<img.*?src=\".*?\".*?>', content)

            content = re.sub(r'(<img.*?src=\").*?/pictures/(.*?\".*>)',
                             lambda m: m.group(1) + 'http://src.1zlab.com/' + relative_path + '/' + m.group(2), content)
            new_list = re.findall(r'<img.*?src=\".*?\".*?>', content)

            for i in range(1, len(new_list)):
                print(origin_list[i], '->', new_list[i])

        return content

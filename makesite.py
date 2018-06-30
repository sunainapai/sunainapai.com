#!/usr/bin/env python

# The MIT License (MIT)
#
# Copyright (c) 2018 Sunaina Pai
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""Make static website/blog with Python."""


import os
import shutil
import re
import glob
import sys
import json
import datetime
import random


def fread(filename):
    """Read file and close the file."""
    with open(filename, 'r') as f:
        return f.read()


def fwrite(filename, text):
    """Write content to file and close the file."""
    basedir = os.path.dirname(filename)
    if not os.path.isdir(basedir):
        os.makedirs(basedir)

    with open(filename, 'w') as f:
        f.write(text)


def log(msg, *args):
    """Log message with specified arguments."""
    sys.stderr.write(msg.format(*args) + '\n')


def truncate(text, words=25):
    """Remove tags and truncate text to the specified number of words."""
    return ' '.join(re.sub('(?s)<.*?>', ' ', text).split()[:words])


def read_headers(text):
    """Parse headers in text and yield (key, value, end-index) tuples."""
    for match in re.finditer('\s*<!--\s*(.+?)\s*:\s*(.+?)\s*-->\s*|.+', text):
        if not match.group(1):
            break
        yield match.group(1), match.group(2), match.end()


def rfc_2822_format(date_str):
    """Convert yyyy-mm-dd date string to RFC 2822 format date string."""
    d = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    return d.strftime('%a, %d %b %Y %H:%M:%S +0000')


def read_content(filename):
    """Read content and metadata from file into a dictionary."""
    # Read file content.
    text = fread(filename)

    # Read metadata and save it in a dictionary.
    date_slug = os.path.basename(filename).split('.')[0]
    match = re.search('^(?:(\d\d\d\d-\d\d-\d\d)-)?(.+)$', date_slug)
    content = {
        'date': match.group(1) or '1970-01-01',
        'slug': match.group(2),
        'src': filename,  # Only for logging purpose
    }

    # Read headers.
    end = 0
    for key, val, end in read_headers(text):
        content[key] = val

    # Separate content from headers.
    text = text[end:]

    # Convert Markdown content to HTML.
    if filename.endswith(('.md', '.mkd', '.mkdn', '.mdown', '.markdown')):
        try:
            if _test == 'ImportError':
                raise ImportError('Error forced by test')
            import CommonMark
            text = CommonMark.commonmark(text)
        except ImportError as e:
            log('WARNING: Cannot render Markdown in {}: {}', filename, str(e))

    # Update the dictionary with content text and summary text.
    content.update({
        'content': text,
        'summary': truncate(text),
        'rfc_2822_date': rfc_2822_format(content['date'])
    })

    return content


def render(template, **params):
    """Replace placeholders in template with values from params."""
    for key, val in params.items():
        template = re.sub(r'{{\s*' + key + '\s*}}', str(val), template)
    return template


def read_posts(src):
    """Read all posts into a list."""
    items = []
    for src_path in glob.glob(src):
        content = read_content(src_path)
        items.append(content)
    return sorted(items, key=lambda x: x['date'], reverse=True)


def make_pages(posts, dst, layout, **params):
    """Generate pages from page content."""
    items = []

    for content in posts:
        items.append(content)
        params.update(content)

        if 'blog' in params:
            params['suggestions'] = suggest_posts(posts, params)
            if params['tag'] == 'trip':
                params['list_slug'] = 'trips'
            else:
                params['list_slug'] = 'blog'

        dst_path = render(dst, **params)
        output = render(layout, **params)

        log('Rendering {} => {} ...', content['src'], dst_path)
        fwrite(dst_path, output)


def make_list(posts, dst, list_layout, item_layout, **params):
    """Generate list page for a blog."""
    items = []
    for post in posts:
        item_params = dict(params, **post)
        item = render(item_layout, **item_params)
        items.append(item)

    params['content'] = ''.join(items)
    dst_path = render(dst, **params)
    output = render(list_layout, **params)

    log('Rendering list => {} ...', dst_path)
    fwrite(dst_path, output)


def suggest_posts(posts, params):
    # Filter posts by tag of the current post.
    posts = [(p['slug'], p['title']) for p in posts
             if p['tag'] == params['tag']]

    # Find index of current post in the filtered posts.
    for i, (slug, title) in enumerate(posts):
        if slug == params['slug']:
            current_post_index = i
            break

    # Recommended the latest post.
    chosen_posts = []
    if current_post_index > 0:
        chosen_posts.append(posts[0])

    # Recommend the next newer post w.r.t. to the current post.
    if current_post_index > 1:
        chosen_posts.append(posts[current_post_index - 1])

    # Recommend the next older post w.r.t. to the current post.
    if current_post_index < len(posts) - 1:
        chosen_posts.append(posts[current_post_index + 1])

    # Recommend a random post.
    unchosen_posts = []
    for slug, title in posts:
        if ((slug, title) not in chosen_posts and slug != params['slug']):
            unchosen_posts.append((slug, title))
    if unchosen_posts:
        chosen_posts.append(random.choice(unchosen_posts))

    # Convert list of slugs to HTML.
    html = []
    for slug, title in chosen_posts:
        html.append('<li><a href="/{}/{}/">{}</a></li>\n'
                    .format(params['blog'], slug, title))

    return ''.join(html)


def main():
    # Create a new _site directory from scratch.
    if os.path.isdir('_site'):
        shutil.rmtree('_site')
    shutil.copytree('static', '_site')

    # Default parameters.
    params = {
        'subtitle': ' - Sunaina Pai',
        'author': 'Sunaina Pai',
        #'site_url': 'https://sunainapai.in',
        'site_url': 'http://localhost:8000', # TODO remove
        'start_year': 2014,
        'current_year': datetime.datetime.now().year
    }

    # If params.json exists, load it.
    if os.path.isfile('params.json'):
        params.update(json.loads(fread('params.json')))

    # Load layouts.
    page_layout = fread('layout/page.html')
    post_layout = fread('layout/post.html')
    list_layout = fread('layout/list.html')
    item_layout = fread('layout/item.html')
    home_layout = fread('layout/home.html')
    feed_xml = fread('layout/feed.xml')
    item_xml = fread('layout/item.xml')

    # Combine layouts to form final layouts.
    post_layout = render(page_layout, content=post_layout)
    list_layout = render(page_layout, content=list_layout)
    home_layout = render(page_layout, content=home_layout)

    # Create site pages.
    site_pages = read_posts('content/[!_]*.html')
    make_pages(site_pages, '_site/{{ slug }}/index.html',
               page_layout, **params)

    # Read all blog posts and cache them in a list.
    all_posts = read_posts('content/blog/*.html')

    # Create blog.
    make_pages(all_posts, '_site/{{ blog }}/{{ slug }}/index.html',
               post_layout, blog='blog', **params)

    # Separate posts into blog posts and trip posts.
    blog_posts = [p for p in all_posts if p['tag'] != 'trip']
    trip_posts = [p for p in all_posts if p['tag'] == 'trip']

    # Create blog list pages.
    make_list(blog_posts, '_site/{{ list_slug }}/index.html',
              list_layout, item_layout,
              blog='blog', list_slug='blog', title='Blog', **params)
    make_list(trip_posts, '_site/{{ list_slug }}/index.html',
              list_layout, item_layout,
              blog='blog', list_slug='trips', title='Trips', **params)
    make_list(all_posts, '_site/{{ list_slug }}/index.html',
              list_layout, item_layout,
              blog='blog', list_slug='posts', title='All Posts', **params)

    # Create home page with blog list.
    home_params = dict(params, title=params['author'], subtitle='')
    make_list(blog_posts[:5], '_site/index.html',
              home_layout, item_layout, blog='blog', **home_params)

    # Create RSS feed.
    make_list(blog_posts, '_site/{{ list_slug }}/rss.xml', feed_xml, item_xml,
              blog='blog', list_slug='blog', title="Sunaina's Blog", **params)
    make_list(trip_posts, '_site/{{ list_slug }}/rss.xml', feed_xml, item_xml,
              blog='blog', list_slug='trips', title="Sunaina's Trips", **params)
    make_list(all_posts, '_site/{{ list_slug }}/rss.xml', feed_xml, item_xml,
              blog='blog', list_slug='posts', title="Sunaina's Posts", **params)


# Test parameter to be set temporarily by unit tests.
_test = None


if __name__ == '__main__':
    main()

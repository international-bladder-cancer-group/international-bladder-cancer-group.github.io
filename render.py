from jinja2 import Environment, FileSystemLoader, select_autoescape
from dateutil import parser
import datetime
import os
import shutil
from dataclasses import dataclass
import json

env = Environment(
        loader = FileSystemLoader('templates'),
        autoescape = select_autoescape(['html', 'xml']))

def load(template):
    template = env.get_template(template)
    return template

def get_block_string(template, block_name, **kwargs):
    return ''.join(list(template.blocks[block_name](template.new_context(**kwargs)))).strip()

def process_events(**kwargs):
    past_events = []
    future_events = []
    now = datetime.datetime.now()
    for f in (f for f in os.scandir('templates/events') if f.is_file()):
        template = load('events/' + f.name)

        link = ""
        if 'c_main' in template.blocks:
            link = '.'.join(f.name.split('.')[:-1])
            os.mkdir('docs/events/' + link)
            template.stream(kwargs).dump('docs/events/' + link + '/index.html')

        title = get_block_string(template, 'c_preview_title')
        summary = ""
        if 'c_preview_summary' in template.blocks:
            summary = get_block_string(template, 'c_preview_summary')
        dates = get_block_string(template, 'c_event_date')

        key_date = parser.parse(get_block_string(template, 'c_key_date'))

        event = {
                'title': title,
                'summary': summary,
                'dates': dates,
                'link': link,
                'key_date': key_date
                }

        if key_date < now:
           past_events.append(event)
        else:
            future_events.append(event)
    return {
            'past': sorted(past_events, key = lambda e: e['key_date'], reverse = True),
            'future': sorted(future_events, key = lambda e: e['key_date'], reverse = False)
            }

def process_previews(collection, sortf = lambda f: f.name, **kwargs):
    previews = []
    for f in sorted(
            [f for f in os.scandir('templates/' + collection) if f.is_file()],
            key = sortf):

        template = load(collection + '/' + f.name)

        link = '.'.join(f.name.split('.')[:-1])
        summary = get_block_string(template, 'c_preview_summary')
        title = get_block_string(template, 'c_preview_title')

        previews.append({
            'link': link,
            'summary': summary,
            'title': title})

        path = 'docs/' + collection + '/' + link
        os.mkdir(path)
        template.stream(kwargs).dump(path + '/index.html', encoding='utf-8')

    return previews

def get_newsletters():
    newsletters = []
    for f in sorted([f for f in os.scandir('sources/newsletters') if f.is_file()],
                    key = lambda f: f.name, reverse=True):
        newsletters.append({
            'file': '/newsletter-issues/' + f.name,
            'title': ' vol. '.join(f.name.split('.')[:-1])
            })
    return newsletters

def process_mission():
    os.mkdir('docs/mission')
    template = load('mission.html')

    template.stream().dump('docs/mission/index.html')

    return get_block_string(template, 'c_preview_summary')


@dataclass
class Person:
    id: int
    name: str
    title: str
    positions: list[str]
    image_url: str

def process_people():
    os.mkdir('docs/members/people')
    shutil.copytree('sources/people/pics', 'docs/members/people/pics')

    people = {}

    for f in sorted([f for f in os.scandir('sources/people/bios') if f.is_file()],
                    key = lambda f: f.name):
        person_dict = json.load(open(f.path))
        image_url = '/members/people/pics/' + str(person_dict['id']).zfill(3) + '.jpg'

        p = Person(
                person_dict['id'],
                person_dict['name'],
                person_dict['title'],
                person_dict['positions'],
                image_url)

        people[p.id] = p

    return people

shutil.rmtree('docs')
os.mkdir('docs')
os.mkdir('docs/members')
os.mkdir('docs/collaborations')
os.mkdir('docs/events')
os.mkdir('docs/library')
os.mkdir('docs/contact')
shutil.copy('sources/CNAME', 'docs')
shutil.copy('sources/style.css', 'docs')
shutil.copy('sources/style.css.map', 'docs')
shutil.copy('sources/style.css.map', 'docs')
shutil.copy('sources/houstonnight.jpg', 'docs')
shutil.copy('sources/logo.jpeg', 'docs')

shutil.copytree('sources/newsletters', 'docs/newsletter-issues')
shutil.copytree('sources/documents', 'docs/documents')

events = process_events()
mission_summary = process_mission()
people = process_people()

load('members.html').stream(
        people = people
        ).dump('docs/members/index.html')
load('collaborations.html').stream(
        collaborations = process_previews(
            'collaborations',
            lambda f: chr(0) + f.name if 'urotoday' in f.name else f.name,
            people = people
            )
        ).dump('docs/collaborations/index.html')
load('events.html').stream(
        events = events
        ).dump('docs/events/index.html')
load('library.html').stream(
        library = process_previews('library',
                                   lambda f: chr(0) + f.name if 'newsletter' in f.name else f.name,
                                   issues=get_newsletters())
        ).dump('docs/library/index.html')
load('contact.html').stream().dump('docs/contact/index.html')

load('home.html').stream(
        mission_summary = mission_summary,
        next_event = events['future'][0],
        last_event = events['past'][0]
        ).dump('docs/index.html')


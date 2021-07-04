
import requests

from time import sleep, time
from os import makedirs, getpid, utime
from os.path import join, isfile, splitext, abspath
from typing import Any, List, Iterable, Optional, Tuple, Union
from sys import exit, stdout
from vk_api import VkApi, VkTools, ApiHttpError
from vk_api.exceptions import ApiError as VKApiErrorExc
from dataclasses import dataclass
from tempfile import gettempdir
from filecmp import cmp as fcmp
from argparse import ArgumentParser
from getpass import getpass
from logging import (warning, info, debug, critical, basicConfig, DEBUG, INFO,
                     getLevelName)

def _no_trace():
  pass

try:
  from ipdb import set_trace
except ImportError:
  set_trace = _no_trace

@dataclass
class Me:
  pass

@dataclass
class Args:
  login:str
  password:str
  targetuser:Union[str,int,Me]
  ignore_album:List[str]
  verbose:int # logging.INFO|logging.DEBUG|...
  interactive:bool
  output:str

SAVEDIR:str="_vk_photo_reclaimer"
SESSION = requests.Session()

Url=str
@dataclass
class UserId:
  val:int

def check_user(vk, uid:Union[str,int,Me])->UserId:
  """Checks whether a user or community exists"""
  if isinstance(uid,Me):
    response = vk.users.get()
    return UserId(int(response[0]['id']))
  else:
    try:
      response = vk.users.get(user_ids=uid)
      return UserId(int(response[0]['id']))
    except VKApiErrorExc:
      if isinstance(uid,int):
        response = vk.groups.getById(group_id=-int(uid))
        return UserId(-response[0]['id'])
      else:
        raise

@dataclass
class Album:
  special:Optional[str]
  data:Optional[Any]
  def id(self)->str:
    return self.data['id'] if self.data else (
      self.special if self.special else "invalid_id")
  def title(self)->str:
    return self.data['title'] if self.data else ''
  def descr(self)->str:
    return self.data['description'] if self.data else ""


@dataclass
class Photo:
  data:Any

@dataclass
class Location:
  path:str

def determine_photo_ext(p:Photo)->str:
  return splitext(p.data['sizes'][0]['url'].split('/')[-1].split('?')[0])[1]

def determine_max_photo_res(item)->Url:
  sizes = []
  for size in item['sizes']:
    sizes.append(size['type'])
  if 'w' in sizes:
    return item['sizes'][sizes.index('w')]['url']
  elif 'z' in sizes:
    return item['sizes'][sizes.index('z')]['url']
  elif 'y' in sizes:
    return item['sizes'][sizes.index('y')]['url']
  elif 'x' in sizes:
    return item['sizes'][sizes.index('x')]['url']
  elif 'm' in sizes:
    return item['sizes'][sizes.index('m')]['url']
  elif 's' in sizes:
    return item['sizes'][sizes.index('s')]['url']
  else:
    raise ValueError(f"Unsupported photo item:\n{item}")

def determine_max_video_res(item, save_dir):
  if 'files' in item:
    if 'mp4_1080' in item['files']:
      return item['files']['mp4_1080']
    if 'mp4_720' in item['files']:
      return item['files']['mp4_720']
    if 'mp4_480' in item['files']:
      return item['files']['mp4_480']
    if 'mp4_360' in item['files']:
      return item['files']['mp4_360']
    if 'mp4_240' in item['files']:
      return item['files']['mp4_240']
  raise ValueError(f"Unsupported video item:\n{item}")

def determine_max_media_res(item, save_dir):
  if 'duration' in item:  # Video
    return determine_max_video_res(item, save_dir)
  elif 'video' in item and 'duration' in item['video']:  # Video story
    return determine_max_video_res(item['video'], save_dir)
  elif 'sizes' in item:  # Photo
    return determine_max_photo_res(item)
  elif 'photo' in item and 'sizes' in item['photo']:  # Photo story
    return determine_max_photo_res(item['photo'])
  else:
    raise ValueError(f"Unsupported media item:\n{item}")

def gen_albums(tools, user_id:UserId)->Iterable[Album]:
  try:
    yield Album('wall',None)
    yield Album('profile',None)
    yield Album('saved',None)
    res = tools.get_all('photos.getAlbums', 200, {'owner_id': user_id.val})
    for item in res['items']:
      yield Album(None,item)
  except ValueError:
    critical(f'Failed to get albums for {user_id.val}')

def gen_photos(tools, user_id:UserId, album:Optional[Album])->Iterable[Photo]:
  try:
    if album:
      res = tools.get_all('photos.get', 200, {'owner_id': user_id.val,
                                              'album_id': album.id()})
    for item in res['items']:
      yield Photo(item)
  except ValueError:
    critical(f'Failed to get photos for {user_id.val}')

def _sanitize_name(n:str, default:str='')->str:
  return n if len(n)>0 and \
    all(map(lambda x: x not in n,['\\','/',':','?','*'])) else default

def suggest_path(args:Args, user:UserId, a:Album, p:Photo)->Tuple[str,str]:
  """ Suggest a directory and a filename where to save photo `p` of the album
  `a` """
  an=_sanitize_name(a.title())
  pn=_sanitize_name(p.data['text'])
  d=join(args.output, f"u_{user.val}",
         f"a_{a.id()}{(' '+an) if len(an)>0 else ''}")
  makedirs(d, exist_ok=True)
  nm=f"p_{p.data['id']}"
  nm+=(' '+pn) if len(pn)>0 else ''
  nm+=f"{determine_photo_ext(p)}"
  return d,join(d,nm)

def adesc(a:Album)->str:
  return f'"{a.title()}"' if len(a.title())>0 else a.id()


def save(args:Args, session, user:UserId, a:Album, p:Photo)->Location:
  info(f"Downloading {p.data.get('id')} from {adesc(a)} of user {user.val}")
  d,file_path=suggest_path(args, user,a,p)
  if not isfile(join(d,'README.txt')) and len(a.descr())>0:
    with open(join(d,'README.txt'),'w') as f:
      f.write(a.descr())
  # set_trace()
  if not isfile(file_path):
    url = determine_max_photo_res(p.data)
    # FIXME: 'filename too long'
    with open(file_path, 'wb') as media_file:
      content=None
      for i in range(4):
        try:
          content = session.get(url).content
          break
        except requests.exceptions.ConnectionError:
          sleep(5)
      if content:
        content = session.get(url).content
        media_file.write(content)
      else:
        critical(f'Failed to get contents for {url}')
    file_time = p.data.get('date', time())
    utime(file_path, (file_time, file_time))
  return Location(file_path)

def check_remove(args, session, vk, user:UserId,
                 a:Album, p:Photo, l:Location)->bool:
  _,file_path=suggest_path(args, user,a,p)
  tmp_path=join(gettempdir(),f'_vk_reclaimed_{getpid()}')
  url = determine_max_photo_res(p.data)
  with open(tmp_path, 'wb') as media_file:
    content=None
    for i in range(4):
      try:
        content = session.get(url).content
        break
      except requests.exceptions.ConnectionError:
        sleep(5)
    if content:
      content = session.get(url).content
      media_file.write(content)
    else:
      critical(f'Failed to get contents for {url}')
      # FIXME: check if photo does not exist, return True in this case
      return False
  ok:bool=False
  if fcmp(tmp_path,file_path,shallow=False):
    info(f"Removing {p.data.get('id')} from {adesc(a)} of user {user.val}")
    # print(f'===> Remove {p.data.get("id")} from VK now!')
    try:
      res = vk.photos.delete(owner_id=user.val, photo_id=p.data['id'])
      if isinstance(res,int) and res==1:
        ok=True
      else:
        critical(f"Failed to remove {p.data['id']}, got ApiHttpError {res}")
    except VKApiErrorExc:
      critical(f"Failed to remove {p.data['id']}")
  else:
    critical(f"Files {file_path} and {tmp_path} don't seem to match")
  return ok

def run(args:Args)->None:
  basicConfig(stream=stdout, level=args.verbose)
  vk = VkApi(args.login, args.password)
  vk.auth()
  vk = vk.get_api()
  tools = VkTools(vk)
  reclaimed_photos=[]
  user_id = check_user(vk,args.targetuser)
  debug('User:', user_id.val)
  for album in gen_albums(tools, user_id):
    debug(album)
    for photo in gen_photos(tools, user_id, album):
      debug('  ' + str(photo))
      l=save(args, SESSION, user_id, album, photo)
      reclaimed_photos.append((album,photo,l))

  if args.interactive:
    print()
    print(80*"*")
    print()
    print("Please review the reclaimed files in this folder:")
    print()
    print(f"   {abspath(args.output)}")
    print()
    print("Press Enter to remove the files from VK")
    print("(or press Ctrl+C to break)")
    print()
    print(80*"*")
    print()
    input()
  else:
    info('Skipping interactive confirmation')

  removed_photos=[]
  for item in reclaimed_photos:
    album,photo,loc=item
    if album.title() in args.ignore_album or \
       album.id() in args.ignore_album:
      info(f"Ignoring {photo.data.get('id')} from {adesc(album)} "\
           f"of user {user_id.val}")
    else:
      if check_remove(args, SESSION, vk, user_id, album, photo, loc):
        removed_photos.append((album,photo,loc))

  for a in gen_albums(tools, user_id):
    if a.data is None:
      continue
    s_reclaimed_photos=set([p for a2,p,_ in reclaimed_photos \
                            if a2.id()==a.id()])
    s_removed_photos=set([p for a2,p,_ in removed_photos if a2.id()==a.id()])
    if s_reclaimed_photos == s_removed_photos:
      try:
        info(f"Removing {adesc(a)} of user {user_id.val}")
        res=vk.photos.deleteAlbum(album_id=a.id(),
                                  owner_id=user_id.val)
        if isinstance(res,int) and res==1:
          ok=True
        else:
          critical(f"Failed to remove {a.id()}, got non-ok {res}")
      except VKApiErrorExc as e:
        critical(f"Failed to remove {a.id()}, got error {e}")
    else:
      warning(f"Not removing album {adesc(a)} of {user_id.val} "\
              f"due to unremoved photos: {s_reclaimed_photos-s_removed_photos}")



def args()->Args:
  parser=ArgumentParser(description='Vkontakte photo reclaimer')
  parser.add_argument('UID', metavar="STR|INT|'ME'", nargs='?',
                      type=str, default=None,
                      help=('User identifier, group identifier, short names '
                            'of those, or string "ME"'))
  parser.add_argument('--login', metavar='STR', required=True,
                      type=str, help='VKontakte login')
  parser.add_argument('--password', metavar='STR',
                      type=str, default=None,
                      help=('VKontakte password in clear-text '
                            '(MIND THE SHELL HISTORY!)'))
  parser.add_argument('--password-file', metavar='PATH',
                      type=str, default=None,
                      help='Name of a file with VKontakte password ')
  parser.add_argument('--ignore-album','--ia','-i', metavar='STR',
                      type=str, default=[], action='append',
                      help='Name of albums to ignore, repeatable')
  parser.add_argument('--verbose','-v', metavar="'DEBUG'|'INFO'|...",
                      default='INFO', help='Verbosity level')
  parser.add_argument('--non-interactive','--ni', '-n', action='store_true',
                      help='Do not expect any stdin input')
  parser.add_argument('--output','-o', metavar='PATH', default=SAVEDIR,
                      help='Folder to download the data before removing it')
  a=parser.parse_args()
  if a.password_file:
    assert a.password is None
    with open(a.password_file) as f:
      pass_=f.read()
  elif a.password:
    assert a.password_file is None
    pass_=a.password
  else:
    if a.non_interactive:
      raise ValueError(('In non-interactive mode either --password or '
                        '--password-file are required'))
    pass_=getpass('Password: ')

  verb_= getLevelName(a.verbose)
  if not isinstance(verb_, int):
    verb_=int(a.verbose)

  return Args(a.login,
              pass_, Me() if a.UID is None else a.UID,
              a.ignore_album,
              verb_,
              not a.non_interactive,
              a.output)

if __name__ == '__main__':
  run(args())


VK Photo reclaimer
==================

Here lies a [Script](./src/vk_photo_reclaimer.py) that surely makes your
[Vkontakte](https://vk.com) profile look more official. It moves your all your
~~silly~~ (not silly!) photos from the VK account back to your hard drive.

Seriously, there are [some](https://team29.org/story/dislike/)
[opinions](https://tjournal.ru/news/75081-mozhno-li-sest-za-layk-i-sotrudnichaet-li-vkontakte-so-sledovatelyami-rol-socsetey-v-delah-za-reposty-i-memy)
saying that the VK policy is becoming less and less friendly towards users.
For good or for bad, one possible solution would be stop using their service
for personal communications altogether.

Usage
-----

```
$ python3 ./src/vk_photo_reclaimer.py --login=mail@example.com --password=fooo --ignore-album=wall --ignore-album=profile --verbose=INFO me
```

Disclaimer: The author tried to make the loss of information impossible but he
can't give you a 100% guarantee it is impossible indeed. Use this
script at your own risk.

The script works by:

1. Logging in to VK using the supplied login and password.
2. Downloading all your photos to the hard drive, see `-o` option
3. Asking for confirmation unless `--non-interactive` is set
4. Removing the reclaimed photos from the VK account (The script double-checks the file integrity before sending `delete` API calls). 
   See also `--ignore-album` option.
5. Wiping empty albums from the VK profile

AFAIK, VK doesn't actually remove photos from their servers, but as we may hope,
'deleting' media breaks the link between the media file and owner's identity.

```
vk_photo_reclaimer.py [-h] --login STR [--password STR]
                             [--password-file PATH] [--ignore-album STR]
                             [--verbose 'DEBUG'|'INFO'|...]
                             [--non-interactive] [--output PATH]
                             [STR|INT|'ME']

Vkontakte photo reclaimer

positional arguments:
  STR|INT|'ME'          User identifier, group identifier, short names of
                        those, or string "ME"

optional arguments:
  -h, --help            show this help message and exit
  --login STR           VKontakte login
  --password STR        VKontakte password in clear-text (MIND THE SHELL
                        HISTORY!)
  --password-file PATH  Name of a file with VKontakte password
  --ignore-album STR, --ia STR, -i STR
                        Name of albums to ignore, repeatable
  --verbose 'DEBUG'|'INFO'|..., -v 'DEBUG'|'INFO'|...
                        Verbosity level
  --non-interactive, --ni, -n
                        Do not expect any stdin input
  --output PATH, -o PATH
                        Folder to download the data before removing it
```

Tech details
------------

Network communications are mainly done done via [VK
API](https://github.com/python273/vk_api) library.

A large part of the script's code was borrowed from
[VK-Scrpapper](https://github.com/vanyasem/VK-Scraper). Thanks,
[@vanyasem](https://mastodon.mynameisivan.ru/@vanyasem).

Nix development environment

```
(system) $ nix-shell # Build all the dependenices
(dev) $ ipython
In [1]: from vk_photo_reclaimer import *
... develop
^D
(dev) $ (cd src; python setup.py sdist bdist_wheel; )
(dev) $ ls -1 src/dist/
vk_photo_reclaimer-1.0.0-py3-none-any.whl
vk_photo_reclaimer-1.0.0.tar.gz
```

References
----------

* Python VK API bindings
  - https://github.com/python273/vk_api
  - https://vk-api.readthedocs.io/en/latest/tools.html
* Official VK API documentation
  - https://vk.com/dev
  - https://vk.com/dev/photos.getAlbums
  - https://vk.com/dev/photos.getAll


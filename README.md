# Nightcaste

**Nightcaste** is a 2D Console-based Roguelike game. It is based on classics such as Rogue and Ancient Domains of Mystery aka ADOM.
It is currently in Alpha stage.

The setting, story, many characters and the game rules are based on the **Exalted Role Playing Game** by *White Wolf Publishing*.

For more information, see the docs: //TODO: Create ReadTheDocs-Page

To play / test the game, you need to have Python 2.7.x or later (Not python 3 and up) installed.
Then, in the root directory of the project run the following command to start the game:

`//TODO: Insert start-command here`

If you find any bugs or other problems, please open an issue.

## Installation of Git Media

First install the git-media gem with the following commands:
`
git clone git@github.com:alebedev/git-media.git
cd git-media
sudo gem install bundler
bundle install
gem build git-media.gemspec
gem install git-media-*.gem
`
Then, add the following config to `.git/config`:
`
[git-media]
    transport = scp
    autodownload = false
    scpuser = ncasset
    scphost = pygmalion.servebeer.com
    scppath = ~/nightcaste_assets
`
Of course, you need to have access to the server via ssh key

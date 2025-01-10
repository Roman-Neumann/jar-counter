# Jar Counter

A [Discord](https://discord.com) bot that manages a counter for server members with a slash command interface. Can be used from several Discord servers simultaneously. Written with the [discord.py](https://github.com/Rapptz/discord.py) API wrapper.

## Command overview

| Commands                                  | Description                                  |
| ----------------------------------------- | -------------------------------------------- |
| `/jar help`                               | Show a command overview and description      |
| `/jar contact`                            | Show contact information                     |
| `/jar sync`                               | Sync commands in case of source code changes |
| `/jar setup`                              | Configure different options of the bot       |
| `/jar create`                             | Create a counter                             |
| `/jar add`, `/jar subtract`, `/jar empty` | Add to, subtract from or reset a counter     |
| `/jar show`                               | Show a textual representation of a counter   |
| `/jar edit`, `/jar delete`                | Edit or delete a counter                     |

Some of these commands have modifiers attached to them like needing a moderator role. These can be further inspected by calling the `/jar help` command.

## Setup

> [!IMPORTANT]
> Requires Python **3.8** or above.

The setup process is shown for Windows and Linux. Since my knowledge of Linux is shallow it will focus on one distribution (Linux Mint).

### Source code

If you have git installed you can clone the repository.

```bash
git clone https://github.com/Roman-Neumann/jar-counter.git
```

Alternatively you may download the code and unzip it to a location of your choosing.

All following terminal commands are assumed to be at the location of your source code.

### Virtual environment (optional)

Using a [virtual environment](https://docs.python.org/3/library/venv.html) is recommended. Especially on Linux since modules for the system Python are usually managed by package managers like apt-get.

On Linux Mint you'll need to install the `venv` package first:

```bash
apt install python3-venv
```

Create a virtual environment:

```bash
# Windows
py -m venv .venv

# Linux Mint
python3 -m venv .venv
```

Activate it:

```bash
# Windows
.venv\Scripts\activate.bat

# Linux Mint
source .venv/bin/activate
```

### Dependencies

This project is dependent on discord.py and it's dependencies. To install them run:

```bash
pip install -r requirements.txt
```

### Discord application

Navigate to the [Discord Development Portal](https://discord.com/developers/applications) and login. If you don't have an application setup you can create one via `New Application` and change it's display name, avatar etc.

On the `Bot` tab find `Privileged Gateway Intents` and enable `Message Content Intent`. This is necessary for the bot to use slash commands.

Under `Build-A-Bot ➤ TOKEN` press `Reset Token` and copy the token.

> [!CAUTION]
> DO NOT share this token with people you don't trust.

### Config

Open the `config.ini` file and enter values on the right of the `=`. Values may include spaces and do not need to be surrounded by quotes.

#### Token

Paste your copied token for the `token` entry.

#### Contact

Add contact information for the `contact` entry. You may leave the contact value empty if you don't want to provide one. The contact information will be shown if the `/jar contact` command is called.

If you want to add a mention to your own Discord profile you can include your User ID e.g.: `<@65432109876543210>`. You will have to enable `Developer Mode` to access IDs in Discord. This can be done via the Settings: `APP SETTINGS ➤ Advanced ➤ Developer Mode`. Right clicking on a user will now include a `Copy User ID` option.

> [!WARNING]
> It is recommended to provide your users with contact information to report [out-of-sync issues](#command-synchronization) with the `/jar sync` command.

### Invite link

Again navigate to the [Discord Development Portal](https://discord.com/developers/applications).

On the `OAuth2` tab scroll down to `OAuth2 URL Generator`. Under `Scopes` select `bot` and under `Bot Permissions` select `Use Slash Commands`. Leave `INTEGRATION TYPE` at `Guild Install` and copy the URL.

This URL may be shared with other people to invite your application to their server.

## Running

### Command synchronization

Slash commands of an application need to be registered to Discord before they are available for users in a server. This must be done _once_ before you start hosting for the first time and every time the command interface changes in the source code e.g. possibly after a `git pull`.

Once the commands are available on Discord, your users can invoke the `/jar sync` command to sync the interface.

> [!NOTE]
> If the `/jar sync` command itself is out-of-sync, then only you can resolve the issue.

To sync commands from a terminal you must [activate your virtual environment](#virtual-environment-optional), provided you have one and run:

```bash
# Windows
py -m jar_counter --sync

# Linux Mint
python3 -m jar_counter --sync
```

### Hosting

To host the bot follow the same steps as above, but do not pass the `--sync` flag.

### Convenience scripts

Two scripts are provided to remove the direct interaction with a terminal.

#### Windows

You may run `scripts\sync.bat` to sync commands and `scripts\host.bat` to start hosting.

#### Linux Mint

To execute the scripts when double clicked, you may need to add execution permission first. Either enable the `Allow executing file as program` checkbox after right clicking on a file under `Properties ➤ Permissions ➤ Execute` or in a terminal from the `scripts` directory run:

```bash
chmod +x sync host
```

You may run `scripts/sync` to sync commands and `scripts/host` to start hosting.

import discord
from discord.ext import commands
import requests
import os
import sys
import time
import json
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    ElementClickInterceptedException, NoSuchElementException, WebDriverException, TimeoutException
)
import string
import secrets
from discord.ui import Button, View, Modal, InputText
import loguru

# Read the bot token from the token.txt file
def read_token():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    token_file_path = os.path.join(script_dir, 'token.txt')
    with open(token_file_path, 'r') as file:
        return file.read().strip()

# Get the bot token
TOKEN = read_token()

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Path to the JSON file for storing user accounts
ACCOUNTS_FILE = "user_accounts.json"

# Dictionary to store account information
user_accounts = {}

# Bot status variables
bot_status = "Ready to create 🟢🟢"
status_message = None

# Load account data from file
def load_account_data():
    global user_accounts
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, 'r') as file:
                data = json.load(file)
                if isinstance(data, dict):
                    user_accounts.update(data)
                else:
                    loguru.logger.error("Invalid data format in user_accounts.json. Expected a dictionary.")
        except (json.JSONDecodeError, ValueError) as e:
            loguru.logger.error(f"Failed to load user_accounts.json: {e}")
            user_accounts = {}

# Save account data to file
def save_account_data():
    with open(ACCOUNTS_FILE, 'w') as file:
        json.dump(user_accounts, file, indent=4)

# Get the total number of accounts created
def get_total_accounts_count():
    return sum(len(accounts) for accounts in user_accounts.values())

# When bot is ready
@bot.event
async def on_ready():
    load_account_data()
    loguru.logger.info(f'{bot.user.name} has connected to Discord!')

# Function to disable buttons
async def disable_buttons(view, message):
    for item in view.children:
        item.disabled = True
    await message.edit(view=view)

# Function to enable buttons
async def enable_buttons(view, message):
    for item in view.children:
        item.disabled = False
    await message.edit(view=view)

# Function to update the bot status
async def update_status(channel, status):
    global bot_status, status_message
    bot_status = status
    if status_message:
        try:
            await status_message.edit(content=f"`Bot status: {bot_status}`")
        except discord.errors.NotFound:
            status_message = await channel.send(f"`Bot status: {bot_status}`")
    else:
        status_message = await channel.send(f"`Bot status: {bot_status}`")

# Function to save account information to text file
def save_account_info(account_info):
    text_file = os.path.join("Accounts", "Cookie.txt")
    with open(text_file, 'a', encoding='utf-8') as file:
        file.write(f"Username: {account_info['username']}\nPassword: {account_info['password']}\nCookie: {account_info['cookie']}\n\n\n")

# Function to save login information for AltManager
def save_altmanager_login(account_info):
    text_file2 = os.path.join("Accounts", "AllAccounts.txt")
    with open(text_file2, 'a', encoding='utf-8') as file:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"Username: {account_info['username']}\nPassword: {account_info['password']}\nDate: {current_time}\n\n")

# Function to create accounts
async def create_account(interaction, ctx, message, view, password=None, number_of_accounts: int = 1):
    global bot_status

    # Update bot status
    await update_status(ctx.channel, "Creating account... 🔴🔴")

    # Config
    ActualWindows = 0

    # URLs
    first_names_url = "https://gist.githubusercontent.com/hipposama/63e973f68d68c77d1fe50b0bbdeb1868/raw/edb0b4e14d0154c6e5129ca93b4fbf09ffa5eebd/GenUsername1-forbotkakaku"
    last_names_url = "https://gist.githubusercontent.com/hipposama/d0793ddfa70a5e1509272ec17f5e6957/raw/3fc2233c6977e05cdaecade51b284283dfc50ced/GenUsername2-forbotkakaku"
    bio_url = "https://gist.githubusercontent.com/hipposama/7478edbaac222481253ad0d2ea9d9878/raw/234ae41c103e898e652916e10b01905618d84175/Bio-roblox"
    roblox_url = "https://www.roblox.com/"

    loguru.logger.info("Random username...")
    first_names_response = requests.get(first_names_url)
    loguru.logger.info("Generating username...")
    last_names_response = requests.get(last_names_url)

    # Check if name loading was successful
    if first_names_response.status_code == 200 and last_names_response.status_code == 200:
        first_names = list(set(first_names_response.text.splitlines()))
        last_names = list(set(last_names_response.text.splitlines()))
    else:
        loguru.logger.error("Name loading failed. Re-execute the script.")
        sys.exit()

    # Create folder if it does not exist
    files_path = os.path.dirname(os.path.abspath(__file__))
    text_files_folder = os.path.join(files_path, "Accounts")
    if not os.path.exists(text_files_folder):
        os.makedirs(text_files_folder)

    # Lists of days, months and years
    days = [str(i + 1) for i in range(10, 28)]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    years = [str(i + 1) for i in range(1980, 2004)]

    # Password generator
    def gen_password(length):
        loguru.logger.info("Generating a password...")
        chars = string.ascii_letters + string.digits + "@?^!#$%&/()=\/¬|°_-[]*~+"
        password = ''.join(secrets.choice(chars) for _ in range(length))
        return password

    def purchase_free_items(session):
        params = {
            'category': 'Characters',
            'minPrice': '0',
            'maxPrice': '0',
            'salesTypeFilter': '1',
            'limit': '120',
        }

        response = session.get('https://catalog.roblox.com/v1/search/items', params=params)
        if response.status_code != 200:
            loguru.logger.error("Failed to fetch free items.")
            return None

        items = response.json().get("data", [])
        if not items:
            loguru.logger.error("No free items found.")
            return None

        random_character = random.choice(items)["id"]

        for _ in range(2): # sometimes even if we buy it once, it doesn't fall into inventory
            random_character_id = session.get(f'https://catalog.roblox.com/v1/bundles/details?bundleIds[]={random_character}').json()[0]["product"]["id"]

            csrf_token = session.get(f'https://www.roblox.com/bundles/{random_character}').text.split('"csrf-token" data-token="')[1].split('"')[0]
            session.headers['x-csrf-token'] = csrf_token

            json_data = {
                'expectedPrice': 0,
            }

            response = session.post(
                f'https://economy.roblox.com/v1/purchases/products/{random_character_id}',
                json=json_data,
            )

            response_json = response.json()
            if response_json.get("purchased"):
                assetname = response_json['assetName']
                loguru.logger.success(f"[{assetname}] bundle purchased!")
                return assetname
            else:
                loguru.logger.error("Purchase failed or unexpected response structure.")
                loguru.logger.debug(f"Response: {response_json}")

        return None

    def humanize_avatar(session, userid, mail):
        assetname = purchase_free_items(session)

        if assetname is None:
            loguru.logger.error("Failed to purchase free items.")
            return

        csrftkn = session.get('https://www.roblox.com/my/avatar').text.split('"csrf-token" data-token="')[1].split('"')[0]

        session.headers['authority'] = 'accountsettings.roblox.com'
        session.headers['x-csrf-token'] = csrftkn
        session.headers['x-bound-auth-token'] = 'pro-roblox-uhq-encrypted'

        for _ in range(2): # same bug as purchase
            params = {
                'isEditable': 'false',
                'itemsPerPage': '50',
                'outfitType': 'Avatar',
                }
            response = session.get(
                f'https://avatar.roblox.com/v2/avatar/users/{userid}/outfits',
                params=params,
            )
            outfit_data = response.json().get("data", [])
            if not outfit_data:
                loguru.logger.error("No outfits found.")
                return

            outfit_id = outfit_data[0]["id"]

            response = session.get(f'https://avatar.roblox.com/v1/outfits/{outfit_id}/details')

            assets = response.json().get("assets", [])
            bodyscale = response.json().get("scale", {})
            playerAvatarType = response.json().get("playerAvatarType")

            json_data = {
                'height': int(bodyscale.get('height', 0)),
                'width': int(bodyscale.get('width', 0)),
                'head': int(bodyscale.get('head', 0)),
                'depth': int(bodyscale.get('depth', 0)),
                'proportion': int(bodyscale.get('proportion', 0)),
                'bodyType': int(bodyscale.get('bodyType', 0)),
            }

            session.post('https://avatar.roblox.com/v1/avatar/set-scales',
                                     json=json_data)

            json_data = {
                'assets': assets
            }

            session.post(
                'https://avatar.roblox.com/v2/avatar/set-wearing-assets',
                json=json_data,
            )

            json_data = {
                'playerAvatarType': playerAvatarType,
            }

            session.post(
                'https://avatar.roblox.com/v1/avatar/set-player-avatar-type',
                json=json_data,
            )
        loguru.logger.success(f"[{mail}] avatar applied!")

        csrftkn = session.get(f"https://www.roblox.com/users/{userid}/profile").text.split('"csrf-token" data-token="')[1].split('"')[0]
        session.headers['x-csrf-token'] = csrftkn

        # Set bio
        bio_response = requests.get(bio_url)
        if bio_response.status_code == 200:
            bios = bio_response.text.splitlines()
            selected_bio = random.choice(bios).strip()
            data = {
                'description': selected_bio,
            }
            response = session.post('https://users.roblox.com/v1/description', json=data)
            if response.status_code == 200:
                loguru.logger.success(f"[{mail}] bio applied: {selected_bio}")
            else:
                loguru.logger.error(f"Failed to set bio: {response.text}")
        else:
            loguru.logger.error("Failed to fetch bios.")

        loguru.logger.success(f"[{mail}] humanization finished!")

    async def create_account_async(url, first_names, last_names, user_id, view, password):
        MaxWindows = 1  # Add this line to access the global variable
        nonlocal ActualWindows
        await disable_buttons(view, message)
        for _ in range(number_of_accounts):  # Loop according to the specified number of accounts
            if ActualWindows >= MaxWindows:
                loguru.logger.info(f"Creating... {MaxWindows}/{ActualWindows}")
                time.sleep(1)
                continue
            ActualWindows += 1
        try:
            loguru.logger.info("Starting to create an account...")
            cookie_found = False
            username_found = False
            elapsed_time = 0

            loguru.logger.info("Initializing webdriver...")
            driver = webdriver.Edge()
            driver.set_window_size(1200, 800)
            driver.set_window_position(0, 0)
            driver.get(url)
            time.sleep(2)

            # Explicit waits
            wait = WebDriverWait(driver, 10)
            loguru.logger.info("Accept Cookie")
            try:
                # Wait for "Accept All" button to appear
                accept_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[text()='Accept All']"))
                )
                # Click "Accept All" button
                accept_button.click()
                loguru.logger.info("Clicked on Accept All button")
            except Exception as e:
                loguru.logger.error(f"An error occurred: {e}")

            # HTML items
            loguru.logger.info("Searching for items on the website")
            username_input = wait.until(EC.presence_of_element_located((By.ID, "signup-username")))
            username_error = wait.until(EC.presence_of_element_located((By.ID, "signup-usernameInputValidation")))
            password_input = wait.until(EC.presence_of_element_located((By.ID, "signup-password")))
            day_dropdown = wait.until(EC.presence_of_element_located((By.ID, "DayDropdown")))
            month_dropdown = wait.until(EC.presence_of_element_located((By.ID, "MonthDropdown")))
            year_dropdown = wait.until(EC.presence_of_element_located((By.ID, "YearDropdown")))
            male_button = wait.until(EC.presence_of_element_located((By.ID, "MaleButton")))
            female_button = wait.until(EC.presence_of_element_located((By.ID, "FemaleButton")))
            register_button = wait.until(EC.presence_of_element_located((By.ID, "signup-button")))

            loguru.logger.info("Selecting day...")
            Selection = Select(day_dropdown)
            Selection.select_by_value(secrets.choice(days))
            time.sleep(0.3)

            loguru.logger.info("Selecting month...")
            Selection = Select(month_dropdown)
            Selection.select_by_value(secrets.choice(months))
            time.sleep(0.3)

            loguru.logger.info("Selecting year...")
            Selection = Select(year_dropdown)
            Selection.select_by_value(secrets.choice(years))
            time.sleep(0.3)

            while not username_found:
                loguru.logger.info("Selecting username...")
                username = secrets.choice(first_names) + secrets.choice(last_names) + "_" + str(secrets.choice(range(1, 99999)))
                username_input.clear()
                username_input.send_keys(username)
                time.sleep(1)
                if username_error.text.strip() == "":
                    username_found = True

            if not password:
                password = gen_password(25)

            loguru.logger.info("Selecting password...")
            password_input.send_keys(password)
            time.sleep(0.3)

            loguru.logger.info("Selecting gender...")
            gender = secrets.choice([1, 2])
            if gender == 1:
                driver.execute_script("arguments[0].click();", male_button)  # Use JavaScript to click the male button
            else:
                driver.execute_script("arguments[0].click();", female_button)  # Use JavaScript to click the female button
            time.sleep(0.5)

            loguru.logger.info("Registering account...")
            register_button.click()
            time.sleep(3)

            try:
                driver.find_element("id", "GeneralErrorText")
                driver.quit()
                for i in range(360):
                    loguru.logger.info(f"Limit reached, waiting... {i + 1}/{360}")
                    time.sleep(1)
            except NoSuchElementException:
                try:
                    await ctx.message.delete()
                except discord.errors.NotFound:
                    pass

            # Wait until the cookie is found or the maximum time has passed
            while not cookie_found and elapsed_time < 180:
                loguru.logger.info("Waiting for the cookie...")
                time.sleep(3)
                elapsed_time += 3
                for cookie in driver.get_cookies():
                    if cookie.get('name') == '.ROBLOSECURITY':
                        cookie_found = True
                        break
            if cookie_found:
                loguru.logger.info("Cookie found...")
                creation_time = datetime.now()
                result = {
                    'cookie': cookie.get('value'),
                    'username': username,
                    'password': password,
                    'created_at': creation_time.strftime('%Y-%m-%d %H:%M:%S')
                }

                try:
                    user_id_meta = driver.find_element(By.XPATH, '//meta[@name="user-data"]').get_attribute('data-userid')
                    result['user_id'] = user_id_meta
                    loguru.logger.success(f"User ID retrieved: {user_id_meta}")
                except Exception as e:
                    loguru.logger.error(f"Failed to retrieve user ID: {e}")
                    result['user_id'] = None

                save_account_info(result)
                save_altmanager_login(result)
                if result is not None:
                    loguru.logger.info("Successfully created!")
                    user_id_str = str(interaction.user.id)  # Convert user ID to string
                    if user_id_str not in user_accounts:
                        user_accounts[user_id_str] = []
                    user_accounts[user_id_str].append(result)
                    save_account_data()  # Save updated account data to file

                    session = requests.Session()
                    session.cookies.set('.ROBLOSECURITY', result['cookie'])
                    humanize_avatar(session, user_id_meta, interaction.user.id)

                time.sleep(3)
                ActualWindows -= 1
                loguru.logger.info(f"Open tabs: {ActualWindows}")
                elapsed_days = (datetime.now() - creation_time).days
                code = f"Username: {result['username']}\nPassword: {result['password']}\nCreated {elapsed_days} days ago"
                await interaction.user.send(f'```Your Roblox Account:\n{code}\n```')

        except (ElementClickInterceptedException, NoSuchElementException, WebDriverException, TimeoutException) as e:
            loguru.logger.info(f"Open tabs: {ActualWindows}")
            ActualWindows -= 1
            loguru.logger.error(e)
        finally:
            await enable_buttons(view, message)
            await update_status(ctx.channel, "Ready to create 🟢🟢")
            view = View()

    await create_account_async(roblox_url, first_names, last_names, interaction.user.id, view, password)

# Function to view created accounts
async def my_accounts(ctx_or_interaction):
    if isinstance(ctx_or_interaction, commands.Context):
        user_id_str = str(ctx_or_interaction.author.id)
    else:
        user_id_str = str(ctx_or_interaction.user.id)
    
    if user_id_str in user_accounts and user_accounts[user_id_str]:
        accounts = user_accounts[user_id_str]
        account_list = "\n\n".join([
            f"Username: {acc['username']}\nPassword: {acc['password']}\nCreated {(datetime.now() - datetime.strptime(acc['created_at'], '%Y-%m-%d %H:%M:%S')).days} days ago"
            for acc in accounts
        ])
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.author.send(f"```Your Accounts:\n\n{account_list}```")
        else:
            await ctx_or_interaction.user.send(f"```Your Accounts:\n\n{account_list}```")
    else:
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.author.send("You have not created any accounts yet.")
        else:
            await ctx_or_interaction.user.send("You have not created any accounts yet.")

# Command to view created accounts
@bot.command(name='my_accounts')
async def my_accounts_command(ctx):
    await my_accounts(ctx)

# Command to view the total number of created accounts
@bot.command(name='total_accounts')
async def total_accounts(ctx):
    total = get_total_accounts_count()
    await ctx.send(f"Total number of created accounts: {total}")

# Modal to input password
class PasswordModal(Modal):
    def __init__(self, interaction, ctx, message, view):
        super().__init__(title="Enter Password")
        self.interaction = interaction
        self.ctx = ctx
        self.message = message
        self.view = view
        self.add_item(InputText(label="Password", placeholder="Enter your desired password (leave empty for random)", required=False))

    async def callback(self, interaction):
        await interaction.response.defer()  # Defer the response immediately
        password = self.children[0].value
        await create_account(self.interaction, self.ctx, self.message, self.view, password)

# Command to show buttons for creating Roblox accounts and viewing created accounts
@bot.command(name='kakaku')
async def roblox_buttons(ctx):
    global status_message

    # Delete the previous message if it exists
    if status_message:
        try:
            await status_message.delete()
        except discord.errors.NotFound:
            pass

    # Button for creating Roblox accounts
    create_button = Button(label="Create Roblox Account", style=discord.ButtonStyle.green)

    async def create_button_callback(interaction):
        modal = PasswordModal(interaction, ctx, message, view)
        await interaction.response.send_modal(modal)

    create_button.callback = create_button_callback

    # Button for viewing created accounts
    view_button = Button(label="View My Accounts", style=discord.ButtonStyle.primary)

    async def view_button_callback(interaction):
        await interaction.response.defer()  # Defer the response immediately
        await my_accounts(interaction)

    view_button.callback = view_button_callback

    # View containing both buttons
    view = View()
    view.add_item(create_button)
    view.add_item(view_button)

    message = await ctx.send("https://i.pinimg.com/originals/b7/d0/48/b7d04806a38e6183ac8e44cc3844ade8.gif", view=view)
    await update_status(ctx.channel, "Ready to create 🟢🟢")
    # Ensure the message exists before trying to delete it
    try:
        await ctx.message.delete()
    except discord.errors.NotFound:
        pass

# Run bot
bot.run(TOKEN)

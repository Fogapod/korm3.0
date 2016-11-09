#-*- coding: utf-8 -*-
# qpy:kivy
import os
import sys
import time
import re
import vk  # depends on requests

from plyer import notification, tts

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.popup import Popup
from kivy.uix.stacklayout import StackLayout


def decode(code):
    key = 0
    for ch in code:
        key += ord(ch)
    key %= 92

    decoded = ''
    txt = open('korm.txt').read()
    for ch in txt:
        if ch == '!':
            decoded += chr(10)
        else:
            if ord(ch) - key < 34:
                ch = chr(ord(ch) - key + 92)
            else:
                ch = chr(ord(ch) - key)

            key += 9
            if key > 92:
                key -= 92

            decoded += ch

    return decoded


def encode(code, txt):
    key = 0
    for ch in code:
        key += ord(ch)
    key %= 92

    encoded = ''

    for ch in txt:
        if ord(ch) == 10:
            encoded += '!'
        else:
            if ord(ch) + key > 127:
                ch = chr(ord(ch) + key - 92)
            else:
                ch = chr(ord(ch) + key)

            key += 9
            if key > 92:
                key -= 92

            encoded += ch

    txt = open('korm.txt', 'w')
    txt.write(encoded)
    txt.close()

# Если файл не обнаружен
if not os.path.isfile('korm.txt'):
    encode('code', '0\n\n\n')

api = None


def vk_request_errors(REQUEST):
    def request_errors(*args):
        #RESPONSE = REQUEST(*args)
        try:
            RESPONSE = REQUEST(*args)
        except Exception as e:
            if str(e) == 'Authorization error (captcha)':
                notification.notify(
                    title=u'Error!', message=u'Captcha!', timeout=5)
            elif str(e) == 'Authorization error (incorrect password)':
                notification.notify(
                    title=u'Error!', message=u'Incorrect password!', timeout=4)
            elif 'Failed to establish a new connection' in str(e) != -1:
                notification.notify(
                    title='Error', message='Check your connection')
            else:
                if api == None:
                    notification.notify(
                        title='Error', message='Authentification required')
                else:
                    notification.notify(title='Error', message=str(e))
            return False
        else:
            return RESPONSE
    return request_errors


@vk_request_errors
def LogInVk(*args):
    LOGIN, PASSWORD = args
    global api
    api = vk.API(vk.AuthSession(app_id="5649665", user_login=LOGIN,
                                user_password=PASSWORD, scope='74752'), v='5.59')

    try:
        tts.speak(u'Добрый день, ' + api.users.get()[0]['first_name'])
    except:
        notification.notify(
            title=u'Error', message=u'Greetings failed!', timeout=2)
    txt = re.split(r'\n', decode('code'))
    encode('code', '%s\n%s\n%s\n' % (txt[0], LOGIN, PASSWORD))
    return True


class LoginScreen(Screen):

    def login(self):
        login = self.ids.login.text
        password = self.ids.pass_input.text

        if login != '' and password != '':
            if LogInVk(re.sub(' ', '', login), re.sub(' ', '', password)):
                self.ids.login.text = ''
                self.ids.pass_input.text = ''
                self.parent.current = 'MP'
        else:
            notification.notify(
                title=u'Error!', message=u'Login and password fields can\'t be empty!', timeout=3)


class Root(ScreenManager):

    @vk_request_errors
    def status_get(*args):
        RESPONSE = api.status.get()
        return RESPONSE

    @vk_request_errors
    def status_set(*args):
        CONTENT = args[1]
        api.status.set(text=CONTENT)
        return True

    @vk_request_errors
    def korm_plus(*args):
        global korm
        try:
            korm += int(args[1])
            is_online = args[2]
        except ValueError:
            notification.notify(
                title='Error!', message='Incorrect enter!')
            return False
        else:
            if is_online:
                api.status.set(
                    text=u'В последний раз получено:%s\nКорма всего [%i]\nПринимается:\n>Вискас\n>Китикет\nЛимит передачи 100млн' % (args[1], korm))
            txt = re.split(r'\n', decode('code'))
            encode('code', '%i\n%s\n%s\n' % (korm, txt[1], txt[2]))
            return str(korm)

    @vk_request_errors
    def korm_minus(*args):
        global korm
        try:
            korm -= int(args[1])
            is_online = args[2]
        except ValueError:
            notification.notify(title='Error!', message='Incorrect enter!')
            return False
        else:
            if is_online:
                api.status.set(
                    text=u'В последний раз потеряно:%s\nКорма всего [%i]\nПринимается:\n>Вискас\n>Китикет\nЛимит передачи 100млн' % (args[1], korm))
            txt = re.split(r'\n', decode('code'))
            encode('code', '%i\n%s\n%s\n' % (korm, txt[1], txt[2]))
            return str(korm)

    def ui_check(self, text):
        text = re.sub('\D', '', text)
        limit = 100000000  # 100 000 000
        if text != '':
            if abs(int(text)) > limit:
                notification.notify(
                    title='Error!', message='Limit is exceeded!')
                return str(limit)

        return text

    def logout(self):
        global api
        api = None
        txt = re.split(r'\n', decode('code'))
        encode('code', '%s\n\n\n' % txt[0])
        self.current = 'LS'

    def refresh_korm(self):
        global korm
        self.ids.korm_counter.title = 'Корма: %i' % korm


class Korm(App):

    def build(self):

        global korm, root
        korm, login_saved, password_saved, trash = re.split(
            r'\n', decode('code'))
        del trash
        korm = int(korm)

        root = Root()

        if login_saved == '' or password_saved == '':
            root.current = 'LS'
        elif not LogInVk(login_saved, password_saved):
            root.current = 'LS'

        root.refresh_korm()
        return root

    def on_pause(self):
        return True

    def on_resume(self):
        pass

    class EmptyStatus(Popup):
        pass

if __name__ == '__main__':
    Korm().run()

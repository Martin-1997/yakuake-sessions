#!/usr/bin/env python
# coding=utf-8

import subprocess as sp, os, math, sys, re
import subprocess
import time
from configparser import ConfigParser
from io import StringIO
from optparse import OptionParser
import dbus
import sys

from .sortedDict import SortedDict

class Ysess:
    # DBUS = 'qdbus org.kde.yakuake '
    # YAKUAKE_DEFAULT_NEW_SESSIONS_OPENED = 1
    # bus = dbus.SessionBus()

    def __init__(self):
        self.bus = bus = dbus.SessionBus()
        self.DBUS = 'qdbus org.kde.yakuake '
        self.YAKUAKE_DEFAULT_NEW_SESSIONS_OPENED = 1


    # Allows arbitrary many input arguments with keywords in **opts
    # These will be available as a dictionary inside the function
    def get_stdout(self, cmd, **opts):
        opts.update({'stdout': sp.PIPE})
        if 'env' in opts:
            env, opts['env'] = opts['env'], os.environ.copy()
            opts['env'].update(env)
        quoted = re.findall(r'".+"', cmd)
        for q in quoted:
            cmd = cmd.replace(q, '%s')
        cmd = cmd.split()
        for i, part in enumerate(cmd):
            if part == '%s':
                cmd[i] = quoted.pop(0)[1:-1]
        proc = sp.Popen(cmd, **opts)
        return proc.communicate()[0].strip()


    def get_yakuake(self, cmd):
        # The calling functions expect a string and not a byte-like object
        return self.get_stdout(self.DBUS + cmd)


    def get_sessions(self, encoding):
        tabs = []
        sessnum = len(self.get_yakuake('/yakuake/sessions terminalIdList').decode(encoding).split(','))
        activesess = int(self.get_yakuake('/yakuake/sessions activeSessionId'))

        sessions = sorted(int(i) for i in self.get_yakuake('/yakuake/sessions sessionIdList').decode(encoding).split(','))
        ksessions = sorted(int(line.split('/')[-1]) for line in self.get_yakuake('').decode(encoding).split('\n') if '/Sessions/' in line)
        session_map = dict(zip(sessions, ksessions))
        last_tabid = None

        for ksession in ksessions:
            # Está dando la sesión del id en el que se hizo el split, no tiene nada que ver con el tab, pero ayuda.
            # Por ejemplo, sesión 4->split->sesión 5->split->sesión 6, dará sesión 5 para la sesión 6.
            # Al usar "sessionAtTab", me devuelve la primera sesión abierta en el tab, lo cual me ayuda a seguir
            # el orden.
            tabid = int(self.get_yakuake('/yakuake/sessions sessionIdForTerminalId %d' % (ksession - 1)))
            split = '' if tabid != last_tabid else ('vertical' if ksession % 2 else 'horizontal')
            last_tabid = tabid
            sessid = int(self.get_yakuake('/yakuake/tabs sessionAtTab %d' % tabid))
            # ksess = '/Sessions/%d' % session_map[sessid]
            ksess = '/Sessions/%d' % ksession
            pid = self.get_yakuake(ksess + ' processId')
            # cat /proc/<pid>/environ
            fgpid = self.get_yakuake(ksess+' foregroundProcessId')
            tabs.append({
                'title': self.get_yakuake('/yakuake/tabs tabTitle %d' % tabid),
                'sessionid': tabid,
                'tabid': tabid,
                'active': sessid == activesess,
                'split': split,
                'cwd': self.get_stdout('pwdx '+pid.decode(encoding)).decode(encoding).partition(' ')[2],
                'cmd': '' if fgpid == pid else self.get_stdout('ps '+fgpid.decode(encoding), env={'PS_FORMAT': 'command'}).decode(encoding).split('\n')[-1],
            })
        return tabs


    def format_sessions(self, tabs, fp, encoding):
        # cp = ConfigParser(dict_type=SortedDict)
        cp = ConfigParser()
        tabpad = int(math.log10(len(tabs))) + 1
        for i, tab in enumerate(tabs):
            print(tab)
            section = ('Tab %%0%dd' % tabpad) % (i+1)
            cp.add_section(section)
            cp.set(section, 'title', tab['title'].decode(encoding))
            cp.set(section, 'active', str(1) if tab['active'] else str(0))
            cp.set(section, 'tab', str(tab['tabid']))
            cp.set(section, 'split', tab['split'])
            cp.set(section, 'cwd', tab['cwd'])
            cp.set(section, 'cmd', tab['cmd'])
        cp.write(fp)


    def clear_sessions(self):
        ksessions = [line for line in self.get_yakuake('').split('\n') if '/Sessions/' in line]
        for ksess in ksessions:
            self.get_yakuake(ksess+' close')


    def load_sessions(self, file):
        cp = ConfigParser(dict_type=SortedDict)
        cp.read_file(file)
        sections = cp.sections()
        if not sections:
            print >>sys.stderr, "No tab info found, aborting"
            sys.exit(1)

        # Clear existing sessions, but only if we have good info (above)
        # clear_sessions()
        subprocess.call(['killall', 'yakuake'])
        # This starts the command and idels until the program (yakuake) is ended - this leads to the problem that the whole calling code is also on hold
        # subprocess.call(['yakuake'])
        subprocess.Popen(['yakuake'])
        time.sleep(1)
        # for section in sections:
        #     get_yakuake('/yakuake/sessions addSession')
        # import time
        # time.sleep(5)

        # Map the new sessions to their konsole session objects
        # sessions = sorted(int(i) for i in get_yakuake('/yakuake/sessions sessionIdList').split(','))
        # ksessions = sorted(int(line.split('/')[-1]) for line in get_yakuake('').split('\n') if '/Sessions/' in line)
        # session_map = SortedDict(zip(sessions, ksessions))

        tab = 0
        active = 0
        # Repopulate the tabs
        for i, section in enumerate(sections):
            opts = dict(cp.items(section))
            if not opts['split']:
                tab += 1
                self.get_yakuake('/yakuake/sessions addSession')
                self.get_yakuake('/yakuake/tabs setTabTitle %d "%s"' % (tab, opts['title']))
            else:
                split_target, split = (tab, opts['split']) if ':' not in opts['split'] else opts['split'].split(':')
                self.get_yakuake('/yakuake/sessions splitTerminal{} {}'.format({'vertical': 'LeftRight',
                                                                        'horizontal': 'TopBottom'}[split],
                                                                        int(split_target)))
            sessid = int(self.get_yakuake('/yakuake/tabs sessionAtTab %d' % i))
            # ksessid = '/Session/%d' % session_map[sessid]
            if opts['cwd']:
                self.get_yakuake('/yakuake/sessions runCommand " cd %s"' % opts['cwd'])
            if opts['cmd']:
                for cmd in opts['cmd'].split(r'\n'):
                    # get_yakuake('/yakuake/sessions runCommand "%s"' % cmd)
                    dbus_session = self.bus.get_object('org.kde.yakuake', '/Sessions/{}'.format(i + 2))
                    dbus_session = dbus.Interface(dbus_session, 'org.kde.konsole.Session')
                    dbus_session.sendText(cmd)
                    dbus_session.sendText('\n')
                    # get_stdout('qdbus org.kde.yakuake /Sessions/%d org.kde.konsole.Session.sendText "%s"' % (i+1, cmd))
                    # get_stdout('qdbus org.kde.yakuake /Sessions/{} org.kde.konsole.Session.sendText "\n"'.format(i+1))
            if opts['active'].lower() in ['y', 'yes', 'true', '1']:
                active = sessid
        if active:
            self.get_yakuake('/yakuake/sessions raiseSession %d' % active)
        # Remove initial session
        self.get_yakuake('/yakuake/sessions removeSession 0')





# -*- coding: utf-8 -*-


import os
import re

from ninja_ide.core import plugin

from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QAbstractItemView
from PyQt4.QtGui import QHeaderView
from PyQt4.QtGui import QTreeWidget
from PyQt4.QtGui import QTreeWidgetItem
from PyQt4.QtGui import QDockWidget

tasknames = ['TODO', 'FIXME', 'OPTIMIZE', 'TEST']


class TaskList(plugin.Plugin):
    def initialize(self):
        #get the services!
        self.main_s = self.locator.get_service('editor')
        self.explorer_s = self.locator.get_service('explorer')

        #explorer
        self._task_widget, self.dock = TaskWidget(self.locator), QDockWidget()
        self.dock.setWindowTitle("Tasks")
        self.dock.setWidget(self._task_widget)
        self.explorer_s.add_tab(self.dock, "Tasks")


class TaskItem(QTreeWidgetItem):
    def __init__(self, parent, content, lineno):
        QTreeWidgetItem.__init__(self, parent, content)
        self.lineno = lineno


class Task:

    def __init__(self, parent, name):
        self.name = name
        self.parent = parent
        self.reg = re.compile("#(\\s)*%s(\\s)*\\:(\\s)*." % name)
        self.root = QTreeWidgetItem(parent, [name])

    def match(self, line, lineno):
        lmatch = self.reg.search(line)
        if lmatch:
            content = line[lmatch.end() - 1:][:75]
            item = TaskItem(self.root, [content], lineno)
            item.setIcon(0, QIcon(self.parent.TASK_IMAGE))


class TaskWidget(QTreeWidget):

    TASK_IMAGE = os.path.join(os.path.dirname(__file__), 'task.png')

    def __init__(self, locator):
        QTreeWidget.__init__(self)
        self.locator = locator
        self._explorer_s = self.locator.get_service('explorer')
        self._main_s = self.locator.get_service('editor')
        #on current tab changed refresh
        self._main_s.currentTabChanged.connect(self._on_tab_changed)
        #on file saved refresh
        self._main_s.fileSaved.connect(self._on_file_saved)

        self.header().setHidden(True)
        self.setSelectionMode(self.SingleSelection)
        self.setAnimated(True)
        self.header().setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.header().setResizeMode(0, QHeaderView.ResizeToContents)
        self.header().setStretchLastSection(False)
        self.setAlternatingRowColors(True)

        self.itemClicked.connect(self._go_to_definition)

    def _on_tab_changed(self):
        self.refresh_tasks()

    def _on_file_saved(self, fileName):
        self.refresh_tasks()

    def refresh_tasks(self):
        editorWidget = self._main_s.get_editor()
        if editorWidget:
            source = self._main_s.get_text()
            self._parse_tasks(source)

    def _go_to_definition(self, item):
        #the root doesn't go to anywhere
        if item.parent() is not None:
            self._main_s.jump_to_line(item.lineno)

    def _parse_tasks(self, source_code):
        self.clear()
        #Task -regex and roots-
        ltasks = []
        for name in tasknames:
            ltasks.append(Task(self, name))

        lines = source_code.split("\n")
        lineno = 0
        for line in lines:
            #apply the regular expressions
            for task in ltasks:
                task.match(line, lineno)
            lineno += 1
        self.expandAll()

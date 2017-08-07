# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) Spyder Project Contributors
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Reports Widget."""

# Standard library imports
import codecs

# Third party imports
from qtpy.QtCore import QUrl, Slot
from qtpy.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QWidget,
                            QTabWidget)

# Spyder-IDE and Local imports
from spyder.widgets.browser import FrameWebView
from spyder.utils.sourcecode import disambiguate_fname
from spyder.widgets.waitingspinner import QWaitingSpinner


class RenderView(FrameWebView):
    """Web widget that shows rendered report."""

    def __init__(self, parent):
        """Initialiaze the WebView."""
        FrameWebView.__init__(self, parent)


class ReportsWidget(QWidget):
    """Reports widget."""

    def __init__(self, parent):
        """Initialiaze ReportsWidget."""
        QWidget.__init__(self, parent)

        self.setWindowTitle("Reports")

        self.tabs = QTabWidget()
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.tabBar().tabMoved.connect(self.move_tab)

        # Progress bar
        self.progress_bar = QWidget(self)
        self.status_text = QLabel(self.progress_bar)
        self.spinner = QWaitingSpinner(self.progress_bar, centerOnParent=False)
        self.spinner.setNumberOfLines(12)
        self.spinner.setInnerRadius(2)
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.spinner)
        progress_layout.addWidget(self.status_text)
        self.progress_bar.setLayout(progress_layout)
        self.progress_bar.hide()

        self.renderviews = {}
        self.filenames = []

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

        self.set_html('', 'Welcome')

    def set_html(self, html_text, fname, base_url=None):
        """Set html text."""
        name = self.disambiguate_fname(fname)
        renderview = self.renderviews.get(fname)

        if 'Welcome' in self.renderviews and renderview is None:
            # Overwrite the welcome tab
            renderview = self.renderviews.pop('Welcome')
            self.renderviews[fname] = renderview
            self.tabs.setTabText(0, name)
            self.filenames[0] = fname

        if renderview is None:
            # create a new renderview
            renderview = RenderView(self)
            self.renderviews[fname] = renderview
            self.tabs.addTab(renderview, name)
            self.filenames.append(fname)

        if base_url is not None:
            renderview.setHtml(html_text, base_url)
        else:
            renderview.setHtml(html_text)

        self.tabs.setCurrentWidget(renderview)

    def set_html_from_file(self, output_fname, input_fname=None):
        """Set html text from a file."""
        if input_fname is None:
            input_fname = output_fname
        html = ""
        with codecs.open(output_fname, encoding="utf-8") as file:
            html = file.read()

        base_url = QUrl()
        self.set_html(html, input_fname, base_url)

    @Slot(str)
    def show_progress(self, fname):
        """Show progress bar and starts spinner.

        Args:
            fname (str): Name of the file being rendered
        """
        self.spinner.start()
        name = self.disambiguate_fname(fname)
        text = "Rendering: {}".format(name)
        self.status_text.setText(text)
        self.progress_bar.show()
        self.set_html('', fname)

    @Slot(bool, object, object)
    def render_finished(self, ok, fname, error):
        """Handle render finish signal.

        If error, displays it, otherwise hide progress bar.

        Args:
            ok (bool): True f the rener was succesful
            fname (str): Name of the file being rendered
            error (str): Error string to display
        """
        self.spinner.stop()
        if error is not None:
            self.status_text.setText(error)
            self.close_tab(self.filenames.index(fname))
        else:
            self.progress_bar.hide()

    def close_tab(self, index):
        """Close tab, and remove its widget form renderviews."""
        fname = self.filenames.pop(index)
        self.renderviews.pop(fname)
        self.tabs.removeTab(index)

    def move_tab(self, start, end):
        """Move self.filenames list to be synchronized when tabs are moved."""
        if start < 0 or end < 0:
            return
        steps = abs(end - start)
        direction = (end - start) // steps  # +1 for right, -1 for left

        fnames = self.filenames
        for i in range(start, end, direction):
            fnames[i], fnames[i + direction] = fnames[i + direction], fnames[i]

    def disambiguate_fname(self, fname):
        """Generate a file name without ambiguation."""
        files_path_list = [filename for filename in self.filenames if filename]
        return disambiguate_fname(files_path_list, fname)

#!/usr/bin/python

#
# wiki.py v0.1
# Copyright 2011 John Wood
#

import re
import sys
import gzip
import getopt
import logging
import urllib2
import StringIO
import pygraphviz as pgv
from BeautifulSoup import BeautifulSoup

def usage():
    print """Usage: wiki.py [-i iterations] [-o outfile] [-p] [-l layout]
-i : iterations, default is 10
-o : outfile, without the file extension. 
     e.g. specifying '-o wiki' (the default)
     will output wiki.log, wiki.dot, and wiki.png
     if -p is specified
-l : layout to be applied. One of 'twopi', 'neato', 
     'dot', 'fdp'. 'dot' is the default. 
-p : print graph as png.
-s : url to start searching from. Must be of the form
     /wiki/foo"""

class Flow:
    def __init__(self, log, max_depth=100):
        self.max_depth = max_depth
        self.flow = []
        self.seen = {}
        self.logger = log
        self.graph = pgv.AGraph(directed=True)
    
    def _HaveSeen(self, link):
        try:
            self.seen[link] = self.seen[link] + 1
        except KeyError:
            self.seen[link] = 1
            return False
        return True

    def GetFlow(self, url=None):
        self.flow = []
        self.logger.info('GetFlow started with {}'.format(url))
        wiki = Wikipedia(self.logger);
        try:
            for i in range(0, self.max_depth):
                wiki.Init(url)
                link = wiki.Parse()
                if not link:
                    return None
                self.logger.info('GetFlow {}'.format(url))
                print link
                self.flow.append(link)
                if self._HaveSeen(link):
                    return self.flow
                url = link
            self.logger.error('GetFlow: Maximum depth reached!')
            return None
        except urllib2.HTTPError, e:
            self.logger.error('GetFlow HTTPError: {} {}'.format(e.code, url))
            return None
        except urllib2.URLError, e:
            self.logger.error('GetFlow URLError: {} {}'.format(e.reason, url))
            return None
    
    def AddFlowToGraph(self, flow):
        self.graph.add_path(flow)

    def DrawGraph(self, dotfile='wiki.dot', image=None, layout='dot'):
        self.logger.info("DrawGraph dotfile={} image={} layout={}".format(dotfile, image, layout))
        self.graph.write(dotfile)
        if image:
            self.graph.layout(prog=layout) 
            self.graph.draw(image)
            
class Wikipedia:
    def __init__(self, log):
        self.logger = log
        self.page = None
        self.url = None
    
    def _GetHtml(self, response):
        headers = response.info()
        self.page = response.read()

        # If the page is large (e.g. /wiki/United_States), sometimes it is gzipped.
        if 'content-encoding' in headers.keys() and headers['content-encoding'] == 'gzip':
            f = StringIO.StringIO(self.page)
            gzipper = gzip.GzipFile(fileobj=f, mode='rb')
            self.page = gzipper.read()
            self.logger.info("_GetHtml {} was gzipped.".format(self.url))

    def Init(self, url=None):
        # We have to spoof wikipedia, since it doesn't allow bots. Shhhhh, don't tell.
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.1 \
                      (KHTML, like Gecko) Ubuntu/11.04 Chromium/14.0.835.202 \
                      Chrome/14.0.835.202 Safari/535.1"

        base = "http://en.wikipedia.org"
        if not url:
            self.url = base + "/wiki/Special:Random"
        else:
            self.url = base + url

        request  = urllib2.Request(self.url, None, {"User-Agent" : user_agent})
        opener   = urllib2.build_opener()
        response = opener.open(request)
        self._GetHtml(response)
    
    def Parse(self):
        soup = BeautifulSoup(self.page)

        # Get the main content.
        main = soup.find('div', {'class':'mw-content-ltr'})
        if not main:
            self.logger.warning("Parse couldn't find mw-content-ltr in {}".format(self.url))
            return None

        # search through <p> tags to find a valid link
        paragraphs = main.findAll('p', recursive=False)
        for p in paragraphs:
            p_str = self._RemoveParenLinks(unicode(p))
            p_soup = BeautifulSoup(p_str)
            # searching with recursive=False guarantees that we won't
            # get any links inside <i> tags.
            links = p_soup.p.findAll('a', recursive=False)
            for l in [l['href'] for l in links]:
                # ignore external links
                if l and re.match('/wiki/.*', l):
                    return l

        self.logger.warning("Parse did not find a link in {}".format(self.url))
        return None

    def _ReplaceParens(self, matchobj):
        return matchobj.group(1) + re.sub(r'[^()]', '', matchobj.group(2)) + matchobj.group(3)

    def _RemoveParenLinks(self, s):
        # remove everything in paretheses that is not in a tag. This prevents
        # us from corrupting links of the form <a href="/wiki/foo_(bar)">baz</a>
        regex = re.compile(r'(>[^<]*?)\((.*?)\)([^>]*?<)')
        while re.search(regex, s): # loop to remove nested parentheses
            s = re.sub(regex, self._ReplaceParens, s)
        return s

def initLogging(logfile='wiki.log'):
    logger    = logging.getLogger('wiki')
    handler   = logging.FileHandler(logfile)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def getArgs(argv):
    try:
        opts, args = getopt.getopt(argv, "i:o:pl:s:")
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit()

    args = {}

    # Set the default values
    args['iterations'] = 10
    args['out']        = 'wiki'
    args['print']      = False
    args['layout']     = 'dot'
    args['start']      = None

    for o, a in opts:
        if o == '-i':
            try:
                args['iterations'] = int(a)
            except ValueError:
                print a, "is not an integer."
                usage()
                sys.exit()
        elif o == '-o':
            args['out'] = a
        elif o == '-p':
            args['print'] = True
        elif o == '-l':
            if a in ['twopi', 'neato', 'dot', 'fdp']:
                args['layout'] = a
            else:
                print a, "must be 'twopi', 'neato', 'dot', or 'fdp'."
                usage()
                sys.exit()
        elif o == '-s':
            if re.match(r'/wiki/.*', a):
                args['start'] = a
            else:
                print a, "must be of the form /wiki/foo."
                usage()
                sys.exit()
        else:
            usage()
            sys.exit()

    args['image']     = None
    if args['print']:
        args['image'] = args['out']+'.png'
    args['logfile']   = args['out']+'.log'
    args['dotfile']   = args['out']+'.dot'

    return args
    
def main(argv):
    args   = getArgs(argv)
    logger = initLogging(args['logfile'])
    flow   = Flow(log=logger)

    for i in range(0, args['iterations']):
        logger.info("Main starting flow {}".format(i+1))
        print "Flow", i+1

        path = flow.GetFlow(args['start'])
        if path:
            flow.AddFlowToGraph(path)

        if i == 0: 
            # We used the start value if there was one,
            # so reset to random.
            args['start'] = None;

    flow.DrawGraph(args['dotfile'], args['image'], args['layout'])

if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        sys.exit()

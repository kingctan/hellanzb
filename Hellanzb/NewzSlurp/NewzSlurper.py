"""
"""
import sys, time
from twisted.internet import reactor
from twisted.news.news import UsenetClientFactory
from twisted.protocols.nntp import NNTPClient
from twisted.python import log
from Hellanzb.Logging import *

__id__ = '$Id$'

class NewzSlurperFactory(UsenetClientFactory):

    def __init__(self):
        """ """
        self.lastChecks = {}

    def buildProtocol(self, addr):
        """ """
        last = self.lastChecks.setdefault(addr, time.mktime(time.gmtime()) - (60 * 60 * 24 * 7))
        #p = nntp.UsenetClientProtocol(self.groups, last, self.storage)
        p = NewzSlurper()
        p.factory = self
        return p

class NewzSlurper(NNTPClient):
    
    def __init__(self):
        """ """
        NNTPClient.__init__(self)
        self.passwords = []
        self.lineCount = 0 # FIXME:

    def authInfo(self, username, password):
        """ """
        info('username is ' + username)
        self.sendLine('AUTHINFO USER ' + username)
        self._newState(None, self.authInfoFailed, self._authInfoUserResponse)
        self.passwords.append(password)

    def _authInfoUserResponse(self, (code, message)):
        """ """
        if code == 381:
            self.sendLine('AUTHINFO PASS ' + self.passwords[0])
            del self.passwords[0]
            self._newState(None, self.authInfoFailed, self._authInfoPassResponse)
        else:
            self.authInfoFailed('%d %s' % (code, message))
        self._endState()

    def _authInfoPassResponse(self, (code, message)):
        """ """
        if code == 281:
            self._authInfoOk('%d %s' % (code, message))
        else:
            self._newState(None, self.authInfoFailed, self.authInfoFailed)
        self._endState()

    def _authInfoOk(self, line):
        "Override for notification when authInfo() action is successful"
        print 'sweet bitch we logged in: ' + line

        self._newState(self.gotIdle,None)

    def authInfoFailed(self, error):
        "Override for notification when authInfoFailed() action fails"
        print 'we didn\'t log in wtfs??: ' + str(error)

    def connectionMade(self):
        global USERNAME
        global PASSWORD
        print 'got connection made'
        NNTPClient.connectionMade(self)
        
        self.authInfo(USERNAME, PASSWORD)

    def gotHead(self, head):
        print 'huh huh i got head'
        print 'head: ' + head

    def getHeadFailed(self, error):
        print 'didn\'t get any head =['
        print 'error: ' + error

    def gotBody(self, body):
        print 'got body'
        # FIXME: decode body. or do it during the lineReceieved()?

    def gotBodyFailed(self, error):
        print 'didn\'t get body'
        print 'error: ' + error

    def lineReceived(self, line):
        self.lineCount += 1
        if self.lineCount % 100 == 0:
            print '.',
        sys.stdout.flush()
        NNTPClient.lineReceived(self, line)

    def gotIdle(self):
        '''Were idle, which means we need to see if theres anything to
        retrieve, and ensure we are in the right group.'''
        print 'idling'
        self.newState(self.gotIdle,None)
        


if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)

    # create factory protocol and application
    nsf = NewzSlurperFactory()

    # connect factory to this host and port
    reactor.connectTCP("unlimited.newshosting.com", 9000, nsf)

    # run
    reactor.run()
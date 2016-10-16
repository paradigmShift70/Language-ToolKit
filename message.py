import datetime


class Message( object ):
   CODES = {
      1:     ( 1, '' )
      }
   
   MESSAGES = [ ]
   
   PRIORITY = {
      1 : 'ERR',
      2 : 'WRN',
      3 : 'INF'
      }
   
   def __init__( self, senderName, senderTag, msgcode, srcmodule, srcline, srccol, **params ):
      self.time         = datetime.datetime.now()
      self.sender       = (senderName,senderTag)
      self.msgcode      = msgcode
      self.srclocation  = (srcmodule,srcline,srccol)
      self.msgParams    = params
      
      self.MESSAGES.append( self )
   
   def __str__( self ):
      msgPriority, msgFormat = self.CODES[self.msgcode]
      parts = {
         'time'         : self.time.strftime("%Y.%m.%d-%H:%M:%S"),
         'priority'     : self.PRIORITY[msgPriority],
         'sender'       : '{:s}#{:s}'.format(*(self.sender)),
         'where'        : '{1:d}:{2:d}({0:s})'.format(*self.srclocation),
         'msgcode'      : self.msgcode,
         'msgExpansion' : msgFormat.format(**self.msgParams)
         }
      return '{:s} '



class InterpreterMessage( object ):
   def __init__( self, errcodeTab ):
      self._errCode = errcodeTab

   def WARN( self, aReporter, errorLocation, errorDetail ):
      self.writeMessage( 'WARN', aReporter, errorLocation, errorDetail )
   
   def ERROR( self, aReporter, whereInCode, detail ):
      self.writeMessage( 'ERR', aReporter, errorLocation, errorDetail )

   def formatMsg( msgType, aReporter, errorLocation, detail ):   
      parts = { }
      parts['time'] = datetime.datetime.now().strftime("%Y-%m-%d/%H:%M:%S")      
      parts['from'] = ''
      locationStr = '{line:d}.{column:d}[{module:s}]'.format( errorLocation.line, errorLocation.column, errorLocation.module )
      from_       = 0
      details     = 0 # location & text expansion of messageCode with args.
      
      '{time:s} {priority:4s} {subject:6s} {from} {details:s} {detail:s} '
   


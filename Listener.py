import ltk_py3.Scanner as Scanner
import traceback
import sys
import datetime
import io
import time
from collections import namedtuple


class EvaluationError( Exception ):
   def __init__( self, excInfo ):
      super().__init__( self, errorMessage )

class Interpreter( object ):
   '''Interpreter interface used by Listener.
   To use the Listener class, the execution environment must be encapsulated
   behind the following interface.
   '''
   def __init__( self ):
      super().__init__()
   
   def reboot( self ):
      '''Reboot the interpreter.'''
      raise NotImplementedError( )
   
   def eval( self, anExprStr, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr ):
      '''Evaluate an expression string of the target language and return a
      string expr representing the result of the evaluation.
      
      Currently, Listener only understands how to deal with eval() that returns
      strings.  Future incarnations of Listener may recognize other return value
      types.
      
      The caller can supply streams to use in place of stdin, stdout and stderr.
      
      EXCEPTIONS:
         Implementation should bundle errors and exceptions such that only
         two kinds of exceptions leave 
      '''
      raise NotImplementedError( )

   def runtimeLibraries( self ):
      '''Return a list of "runtime libraries" for the underlying interpreter.
      The Listener expects these libraries to be written entirely in the
      target language.  The runtime libraries are loaded into the interpreter
      upon interpreter construction, and as part of a call to reboot()'''
      raise NotImplementedError( )
   
   def testFileList( self ):
      '''Return a list of log files for testing the interpreter.  The listener
      re-runs each of the logs files; comparing the output with the output
      recorded in the log file.'''
      raise NotImplementedError( )
   
class Listener( object ):
   '''A generic Listener environment for dynamic languages.
   Heavily ripped-off from Python's own cmd library.'''
   prompt0 = '>>> '
   prompt1 = '... '
   nohelp = "*** No help on %s"
   ruler = '='
   doc_leader = ""
   doc_header = "Documented commands (type help <topic>):"
   misc_header = "Miscellaneous help topics:"
   undoc_header = "Undocumented commands:"

   def __init__( self, anInterpreter, **keys ):
      super().__init__( )

      self._interp     = anInterpreter
      self._history    = [ ]                 # list of ( expr, retVal, stdoutVal, stderrVal )
      self._logFile    = None
      self._exceptInfo = None
      self.writeLn( '{language:s} {version:s}'.format(**keys) )
      self.writeLn( '- Execution environment initialized.' )
      self.do_reboot( [ ] )

   def writeLn( self, value='' ):
      print( value )
      if self._logFile:
         self._logFile.write( value + '\n' )

   def prompt( self, prompt='' ):
      inputStr = input( prompt ).lstrip()
      if self._logFile and ((len(inputStr) == 0) or (inputStr[0] != ']')):
         self._logFile.write( prompt + inputStr + '\n' )
      
      return inputStr.strip( )

   def do_reboot( self, args ):
      '''Usage: reboot
      Reset the interpreter.
      '''
      if len(args) > 0:
         print( self.do_reboot.__doc__ )
         return
      
      if self._logFile:
         print( 'Please close the log before exiting.' )
         return
   
      self._interp.reboot( )
      self._history = [ ]
      
      for libFileName in self._interp.runtimeLibraries():
         self.readAndEvalFile( libFileName )
      print( '- Runtime libraries loaded.' )
      self.writeLn( 'Listener started.' )
      self.writeLn( 'Enter any expression to have it evaluated by the interpreter.')
      self.writeLn( 'Enter \']help\' for listener commands.' )
      self.writeLn( 'Welcome!' )

   def do_log( self, args ):
      '''Usage:  log <filename>
      Begin a new logging session.
      '''
      if len(args) != 1:
         print( self.do_log.__doc__ )
         return

      filename = args[0]
      if self._logFile is not None:
         print( 'Already logging.\n' )
         return

      self._logFile = open( filename, 'w' )
      if self._logFile is None:
         print( 'Unable to open file for writing.' )
         return

      self.writeLn( '>>> ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;' )
      self.writeLn( '... ;;;;;;  Starting Log ( {0} ): {1}\n'.format( datetime.datetime.now().isoformat(), filename ) )
      self.writeLn( '... 0')
      self.writeLn( '' )
      self.writeLn( '==> 0')

   def do_read( self, args ):
      '''Usage:  read <filename> [v|v]
      Read and execute a log file.  V is for verbose.  
      '''
      if len(args) not in ( 1, 2 ):
         print( self.do_read.__doc__ )
         return
      
      verbosity=0
      if len(args) == 2:
         if args[1].upper() == 'V':
            verbosity=3
      
      filename = args[0]
      self.readAndEvalFile( filename, testFile=False, verbosity=verbosity )
      print( 'Log file read successfully: ' + filename )

   def do_test( self, args ):
      '''Usage:  test <filename>
      Test the interpreter using a log file.
      Read and execute a log file;
      comparing the return value to the log file return value.
      '''
      numArgs = len(args)
      if numArgs not in ( 0, 1 ):
         print( self.do_test.__doc__ )
         return
      
      if numArgs == 1:
         filename = args[0]
         filenameList = [ filename ]
      else:
         filenameList = self._interp.testFileList( )
      
      for filename in filenameList:
         self.readAndEvalFile( filename, testFile=True )

   def do_continue( self, args ):
      '''Usage:  continue <filename> [V|v]
      Read and execute a log file.  Keep the log file open to
      continue a logging session where you left off.  V reads
      the file verbosely.
      '''
      numArgs = len(args)
      if numArgs not in ( 1, 2 ):
         print( self.do_continue.__doc__ )
         return
      
      self.do_read( args )
      
      filename = args[0]
      self._logFile = open( filename, 'a' )
      if self._logFile is None:
         print( 'Unable to open file for append.' )
         return
      
      self.writeLn( '>>> ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;' )
      self.writeLn( '... ;;;;;;  Continuing Log ( {0} ): {1}\n'.format( datetime.datetime.now().isoformat(), filename ) )
      self.writeLn( '... 0')
      self.writeLn( '' )
      self.writeLn( '==> 0')

   def do_close( self, args ):
      '''Usage:  close
      Close the current logging session.
      '''
      if len(args) != 0:
         print( self.do_close.__doc__ )
         return
      
      if self._logFile is None:
         print( "Not currently logging." )
         return
      
      self.writeLn( '>>> ;;;;;;  Logging ended.' )
      self.writeLn( '... ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;' )
      self.writeLn( '... 0')
      self.writeLn( '' )
      self.writeLn( '==> 0')
      if self._logFile is not None:
         self._logFile.close( )
      
      self._logFile = None

   def do_dump( self, args ):
      '''Usage:  dump
      Dump a stack trace of the most recent error.
      '''
      if len(args) != 0:
         print( self.do_dump.__doc__ )
         return
      
      if self._exceptInfo is None:
         self.writeLn( 'No exception information available.\n' )
         return
      
      sys.excepthook( *self._exceptInfo )

   def do_exit( self, args ):
      '''Usage:  exit
      Exit the interpreter and listener.
      '''
      if len(args) != 0:
         print( self.do_exit.__doc__ )
         return
      
      self.writeLn( 'Bye.' )
      raise Exception( )

   def do_help(self, args ):
      '''Usage: help [<command>]
      List all available commands, or detailed help for a specific command.
      '''
      if len(args) > 0:
         arg = args[0]
         # XXX check arg syntax
         try:
            doc=getattr(self, 'do_' + arg).__doc__
            if doc:
               print("%s"%str(doc))
               return
         except AttributeError:
            pass
         print("%s"%str(self.nohelp % (arg,)))
         return
      else:
         names = self.get_names()
         cmds_doc = []
         cmds_undoc = []
         help = {}
         for name in names:
            if name[:5] == 'help_':
               help[name[5:]]=1
         names.sort()
         # There can be duplicates if routines overridden
         prevname = ''
         for name in names:
            if name[:3] == 'do_':
               if name == prevname:
                  continue
               prevname = name
               cmd=name[3:]
               if cmd in help:
                  cmds_doc.append(cmd)
                  del help[cmd]
               elif getattr(self, name).__doc__:
                  cmds_doc.append(cmd)
               else:
                  cmds_undoc.append(cmd)
         print("%s"%str(self.doc_leader))
         self.print_topics(self.doc_header,   cmds_doc,   15,80)
         self.print_topics(self.misc_header,  list(help.keys()),15,80)
         self.print_topics(self.undoc_header, cmds_undoc, 15,80)

   def get_names( self ):
      # This method used to pull in base class attributes
      # at a time dir() didn't do it yet.
      return dir(self.__class__)

   def print_topics(self, header, cmds, cmdlen, maxcol):
      if cmds:
         print("%s"%str(header))
         if self.ruler:
            print("%s"%str(self.ruler * len(header)))
         self.columnize(cmds, maxcol-1)
         print()

   def columnize(self, list, displaywidth=80):
      """Display a list of strings as a compact set of columns.

      Each column is only as wide as necessary.
      Columns are separated by two spaces (one was not legible enough).
      """
      if not list:
         print("<empty>")
         return

      nonstrings = [i for i in range(len(list))
                    if not isinstance(list[i], str)]
      if nonstrings:
         raise TypeError("list[i] not a string for i in %s"
                         % ", ".join(map(str, nonstrings)))
      size = len(list)
      if size == 1:
         print('%s'%str(list[0]))
         return
      # Try every row count from 1 upwards
      for nrows in range(1, len(list)):
         ncols = (size+nrows-1) // nrows
         colwidths = []
         totwidth = -2
         for col in range(ncols):
            colwidth = 0
            for row in range(nrows):
               i = row + nrows*col
               if i >= size:
                  break
               x = list[i]
               colwidth = max(colwidth, len(x))
            colwidths.append(colwidth)
            totwidth += colwidth + 2
            if totwidth > displaywidth:
               break
         if totwidth <= displaywidth:
            break
      else:
         nrows = len(list)
         ncols = 1
         colwidths = [0]
      for row in range(nrows):
         texts = []
         for col in range(ncols):
            i = row + nrows*col
            if i >= size:
               x = ""
            else:
               x = list[i]
            texts.append(x)
         while texts and not texts[-1]:
            del texts[-1]
         for col in range(len(texts)):
            texts[col] = texts[col].ljust(colwidths[col])
         print("%s"%str("  ".join(texts)))

   def doCommand( self, listenerCommand ):
      cmdParts  = listenerCommand[1:].split( ' ' )
      cmdParts  = [ x for x in cmdParts if x != '' ]
      cmd,*args = cmdParts
      
      try:
         func = getattr(self, 'do_' + cmd)
      except AttributeError:
         print( 'Unknown command "{:s}"'.format(listenerCommand) )
      
      func(args)

   def readEvalPrintLoop( self ):
      inputExprStr = ''

      while True:
         if inputExprStr == '':
            lineInput = self.prompt( '>>> ' )
         else:
            lineInput = self.prompt( '... ' )

         if (lineInput == '') and (inputExprStr != ''):
            if inputExprStr[0] == ']':
               self.doCommand( inputExprStr[:-1] )
            else:
               try:
                  resultStr = self._interp.eval( inputExprStr )
                  self.writeLn( '\n==> ' + resultStr )

               except Scanner.ParseError as ex:
                  self._exceptInfo = sys.exc_info( )
                  self.writeLn( ex.generateVerboseErrorString() )

               except EvaluationError as ex:
                  self._exceptInfo = sys.exc_info( )
                  self.writeLn( ex.args[-1] )

               except Exception as ex:
                  self._exceptInfo = sys.exc_info( )
                  self.writeLn( ex.args[-1] )

               self.writeLn( )
            
            inputExprStr = ''
            
         else:
            inputExprStr += (lineInput.strip() + '\n')

   def readAndEvalFile( self, filename, testFile=False, verbosity=0 ):
      inputText = None
      with open( filename, 'r') as file:
         inputText = file.read( )
      
      if inputText is None:
         self.writeLn( 'Unable to read file.\n' )
         return
      
      if testFile:
         print( '   Test file: {0}... '.format(filename), end='' )
         self._sessionLog_test( inputText, verbosity )
      else:
         return self._sessionLog_restore( inputText, verbosity )

   def _sessionLog_restore( self, inputText, verbosity=0 ):
      exprNum = 0
      
      implStdOut = io.StringIO()
      for exprNum,exprPackage in enumerate(self._iterLog(inputText)):
         exprStr,outputStr,retValStr = exprPackage
         if verbosity == 0:
            self._interp.eval( exprStr, stdout=implStdOut )
         else:
            exprLines = exprStr.splitlines()
            print( '\n>>> {:s}'.format(exprLines[0]) )
            for line in exprLines[1:]:
               print( '... {:s}'.format(line) )
            
            resultStr = self._interp.eval( exprStr )
            print( '\n==> ' + resultStr )
         exprNum += 1
      
      return exprNum
   
   def _sessionLog_test( self, inputText, verbosity=0 ):
      numPassed = 0
      
      if verbosity >= 3:
         print()
      
      implStdOut = io.StringIO()
      for exprNum,exprPackage in enumerate(self._iterLog(inputText)):
         exprStr,expectedOutput,expectedRetValStr = exprPackage
         resultExpr = self._interp.eval( exprStr, stdout=implStdOut )
      
         # Test stdio output
         #outputText = implStdOut.getvalue()
         #if outputText == expectedOutput:
            #outputTest_passed = True
            #outputTest_reason = 'PASSED!'
         #else:
            #outputTest_passed = False
            #outputTest_reason = 'Failed!  Output value doesn\'t equal expected value.'
      
         # Test Return Value
         if (resultExpr is None) and (expectedRetValStr is not None):
            retValTest_passed = False
            retValTest_reason = 'Failed!  Returned <Code>None</Code>; expected <i>value</i>.'
         elif (resultExpr is not None) and (expectedRetValStr is None):
            retValTest_passed = False
            retValTest_reason = 'Failed!  Returned a value; expected <Code>None</Code>'
         elif (resultExpr is not None) and (expectedRetValStr is not None):
            if resultExpr == expectedRetValStr:
               retValTest_passed = True
               retValTest_reason = 'PASSED!'
            else:
               retValTest_passed = False
               retValTest_reason = 'Failed!  Return value doesn\'t equal expected value.'
      
         # Determine Pass/Fail
         #if outputTest_passed and retValTest_passed:
         if retValTest_passed:
            test_passed = True
            test_reason = 'PASSED!'
            numPassed += 1
         else:
            test_passed = False
            test_reason = 'Failed!'
      
         if verbosity >= 3:
            print( '     {0}. {1}'.format(str(exprNum).rjust(6), test_reason) )
   
      numTests = exprNum + 1
      numFailed = numTests - numPassed
      if test_passed:
         print( 'PASSED!' )
      else:
         print( '({0}/{1}) Failed.'.format(numFailed,numTests) )
  
   def evalAndRecord( self, inputText, printresult=False, printstdout=False ):
      stdout = io.StringIO();
      stderr = io.StringIO();
      retVal = self._interp.eval( inputText, stdout=stdout, stderr=stderr )
      stdout.flush()
      stderr.flush()
      card = ( inputText, retVal, stdout.getvalue(), stderr.getvalue() )
      self._history.append( card )

   def _iterLog( self, inputText ):
      stream = Scanner.ScannerLineStream( inputText )
      
      while True:
         # Skip empty and comment lines
         line = stream.peekLine()
         strippedLine = line.strip()
         while (strippedLine == '') or strippedLine.startswith( ';' ):
            stream.consumeLine()
            line = stream.peekLine()
            strippedLine = line.strip()
         
         if not line.startswith( '>>> ' ):
            raise Exception()
         
         # Parse Expression
         expr = line[ 4: ]
         stream.consumeLine()
         line = stream.peekLine()
         while line.startswith( '... ' ):
            expr += line[ 4: ]
            stream.consumeLine()
            line = stream.peekLine()
         
         output = None
         while not line.startswith( ('==> ','... ','>>> ') ):
            # Parse written output
            if output is None:
               output = ''
            output += line
            stream.consumeLine()
            line = stream.peekLine()
         if output:
            output = output[ : -1 ]        # remove the newline character at the end of output
         
         retVal = None
         if line.startswith( '==> ' ):
            retVal = line[ 4: ]
            stream.consumeLine()
            line = stream.peekLine()
            while not line.startswith( ('==> ','... ','>>> ') ):
               retVal += line
               stream.consumeLine()
               line = stream.peekLine()
            retVal = retVal[ : -2 ]       # remove the two newline characters at the end of retVal
         
         yield expr,output,retVal
   


class StreamTee( object ):
   def __init__( self, *streams ):
      self._strms = streams
      self.closed = False
   
   def write( self, strVal ):
      for strm in self._strms:
         strm.write( strVal )
   
   def flush( self ):
      for strm in self._strms:
         strm.flush( )
   
   def isatty( self ):
      return False

   def readable( self ):
      return False
   
   def seekable( self ):
      return False

   def writeable( self ):
      return True

   def close( self ):
      for strm in self._strms:
         strm.close( )
      self.closed = True

Card = namedtuple( 'Card', ['expression','response','parse_err','eval_err','console','cost'] )

class Listener_New( object ):
   '''A generic Listener environment for dynamic languages.
   Heavily ripped-off from Python's own cmd library.'''
   prompt0 = '>>> '
   prompt1 = '... '
   nohelp = "*** No help on %s"
   ruler = '='
   doc_leader = ""
   doc_header = "Documented commands (type help <topic>):"
   misc_header = "Miscellaneous help topics:"
   undoc_header = "Undocumented commands:"

   def __init__( self, anInterpreter, **keys ):
      super().__init__( )

      self._interp     = anInterpreter
      self._history    = [ ]                 # list of ( expr, retVal, stdoutVal, stderrVal )
      self._logFile    = None
      self._exceptInfo = None
      self.writeLn( '{language:s} {version:s}'.format(**keys) )
      self.writeLn( '- Execution environment initialized.' )
      self.do_reboot( [ ] )

   def writeLn( self, value='' ):
      print( value )
      if self._logFile:
         self._logFile.write( value + '\n' )

   def prompt( self, prompt='' ):
      inputStr = input( prompt ).lstrip()
      if self._logFile and ((len(inputStr) == 0) or (inputStr[0] != ']')):
         self._logFile.write( prompt + inputStr + '\n' )
      
      return inputStr.strip( )

   def do_reboot( self, args ):
      '''Usage: reboot
      Reset the interpreter.
      '''
      if len(args) > 0:
         print( self.do_reboot.__doc__ )
         return
      
      if self._logFile:
         print( 'Please close the log before exiting.' )
         return
   
      self._interp.reboot( )
      self._history = [ ]
      
      for libFileName in self._interp.runtimeLibraries():
         self.readAndEvalFile( libFileName )
      print( '- Runtime libraries loaded.' )

   def do_log( self, args ):
      '''Usage:  log <filename>
      Begin a new logging session.
      '''
      if len(args) != 1:
         print( self.do_log.__doc__ )
         return

      filename = args[0]
      if self._logFile is not None:
         print( 'Already logging.\n' )
         return

      self._logFile = open( filename, 'w' )
      if self._logFile is None:
         print( 'Unable to open file for writing.' )
         return

      self.writeLn( '>>> ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;' )
      self.writeLn( '... ;;;;;;  Starting Log ( {0} ): {1}\n'.format( datetime.datetime.now().isoformat(), filename ) )
      self.writeLn( '... 0')
      self.writeLn( '' )
      self.writeLn( '==> 0')

   def do_read( self, args ):
      '''Usage:  read <filename> [v|v]
      Read and execute a log file.  V is for verbose.  
      '''
      if len(args) not in ( 1, 2 ):
         print( self.do_read.__doc__ )
         return
      
      verbosity=0
      if len(args) == 2:
         if args[1].upper() == 'V':
            verbosity=3
      
      filename = args[0]
      self.readAndEvalFile( filename, testFile=False, verbosity=verbosity )
      print( 'Log file read successfully: ' + filename )

   def do_test( self, args ):
      '''Usage:  test <filename>
      Test the interpreter using a log file.
      Read and execute a log file;
      comparing the return value to the log file return value.
      '''
      numArgs = len(args)
      if numArgs not in ( 0, 1 ):
         print( self.do_test.__doc__ )
         return
      
      if numArgs == 1:
         filename = args[0]
         filenameList = [ filename ]
      else:
         filenameList = self._interp.testFileList( )
      
      for filename in filenameList:
         self.readAndEvalFile( filename, testFile=True )

   def do_continue( self, args ):
      '''Usage:  continue <filename> [V|v]
      Read and execute a log file.  Keep the log file open to
      continue a logging session where you left off.  V reads
      the file verbosely.
      '''
      numArgs = len(args)
      if numArgs not in ( 1, 2 ):
         print( self.do_continue.__doc__ )
         return
      
      self.do_read( args )
      
      filename = args[0]
      self._logFile = open( filename, 'a' )
      if self._logFile is None:
         print( 'Unable to open file for append.' )
         return
      
      self.writeLn( '>>> ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;' )
      self.writeLn( '... ;;;;;;  Continuing Log ( {0} ): {1}\n'.format( datetime.datetime.now().isoformat(), filename ) )
      self.writeLn( '... 0')
      self.writeLn( '' )
      self.writeLn( '==> 0')

   def do_close( self, args ):
      '''Usage:  close
      Close the current logging session.
      '''
      if len(args) != 0:
         print( self.do_close.__doc__ )
         return
      
      if self._logFile is None:
         print( "Not currently logging." )
         return
      
      self.writeLn( '>>> ;;;;;;  Logging ended.' )
      self.writeLn( '... ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;' )
      self.writeLn( '... 0')
      self.writeLn( '' )
      self.writeLn( '==> 0')
      if self._logFile is not None:
         self._logFile.close( )
      
      self._logFile = None

   def do_dump( self, args ):
      '''Usage:  dump
      Dump a stack trace of the most recent error.
      '''
      if len(args) != 0:
         print( self.do_dump.__doc__ )
         return
      
      if self._exceptInfo is None:
         self.writeLn( 'No exception information available.\n' )
         return
      
      sys.excepthook( *self._exceptInfo )

   def do_exit( self, args ):
      '''Usage:  exit
      Exit the interpreter and listener.
      '''
      if len(args) != 0:
         print( self.do_exit.__doc__ )
         return
      
      self.writeLn( 'Bye.' )
      raise Exception( )

   def do_help(self, args ):
      '''Usage: help [<command>]
      List all available commands, or detailed help for a specific command.
      '''
      if len(args) > 0:
         arg = args[0]
         # XXX check arg syntax
         try:
            doc=getattr(self, 'do_' + arg).__doc__
            if doc:
               print("%s"%str(doc))
               return
         except AttributeError:
            pass
         print("%s"%str(self.nohelp % (arg,)))
         return
      else:
         names = self.get_names()
         cmds_doc = []
         cmds_undoc = []
         help = {}
         for name in names:
            if name[:5] == 'help_':
               help[name[5:]]=1
         names.sort()
         # There can be duplicates if routines overridden
         prevname = ''
         for name in names:
            if name[:3] == 'do_':
               if name == prevname:
                  continue
               prevname = name
               cmd=name[3:]
               if cmd in help:
                  cmds_doc.append(cmd)
                  del help[cmd]
               elif getattr(self, name).__doc__:
                  cmds_doc.append(cmd)
               else:
                  cmds_undoc.append(cmd)
         print("%s"%str(self.doc_leader))
         self.print_topics(self.doc_header,   cmds_doc,   15,80)
         self.print_topics(self.misc_header,  list(help.keys()),15,80)
         self.print_topics(self.undoc_header, cmds_undoc, 15,80)

   def get_names( self ):
      # This method used to pull in base class attributes
      # at a time dir() didn't do it yet.
      return dir(self.__class__)

   def print_topics(self, header, cmds, cmdlen, maxcol):
      if cmds:
         print("%s"%str(header))
         if self.ruler:
            print("%s"%str(self.ruler * len(header)))
         self.columnize(cmds, maxcol-1)
         print()

   def columnize(self, list, displaywidth=80):
      """Display a list of strings as a compact set of columns.

      Each column is only as wide as necessary.
      Columns are separated by two spaces (one was not legible enough).
      """
      if not list:
         print("<empty>")
         return

      nonstrings = [i for i in range(len(list))
                    if not isinstance(list[i], str)]
      if nonstrings:
         raise TypeError("list[i] not a string for i in %s"
                         % ", ".join(map(str, nonstrings)))
      size = len(list)
      if size == 1:
         print('%s'%str(list[0]))
         return
      # Try every row count from 1 upwards
      for nrows in range(1, len(list)):
         ncols = (size+nrows-1) // nrows
         colwidths = []
         totwidth = -2
         for col in range(ncols):
            colwidth = 0
            for row in range(nrows):
               i = row + nrows*col
               if i >= size:
                  break
               x = list[i]
               colwidth = max(colwidth, len(x))
            colwidths.append(colwidth)
            totwidth += colwidth + 2
            if totwidth > displaywidth:
               break
         if totwidth <= displaywidth:
            break
      else:
         nrows = len(list)
         ncols = 1
         colwidths = [0]
      for row in range(nrows):
         texts = []
         for col in range(ncols):
            i = row + nrows*col
            if i >= size:
               x = ""
            else:
               x = list[i]
            texts.append(x)
         while texts and not texts[-1]:
            del texts[-1]
         for col in range(len(texts)):
            texts[col] = texts[col].ljust(colwidths[col])
         print("%s"%str("  ".join(texts)))

   def doCommand( self, listenerCommand ):
      cmdParts  = listenerCommand[1:].split( ' ' )
      cmdParts  = [ x for x in cmdParts if x != '' ]
      cmd,*args = cmdParts
      
      try:
         func = getattr(self, 'do_' + cmd)
      except AttributeError:
         print( 'Unknown command "{:s}"'.format(listenerCommand) )
      
      func(args)

   def readEvalPrintLoop( self ):
      self.writeLn( 'Listener started.' )
      self.writeLn( 'Enter any expression to have it evaluated by the interpreter.')
      self.writeLn( 'Enter \']help\' for listener commands.' )
      self.writeLn( 'Welcome!' )
      inputExprStr = ''

      while True:
         if inputExprStr == '':
            newCardNum = len(self._history)
            promptStr = ']] === [ {:d} ] ======================================'.format( newCardNum )
            print( promptStr )
            lineInput = input( )
            #lineInput = self.prompt( '>>> ' )
         else:
            lineInput = input( )
            #lineInput = self.prompt( '... ' )

         if (lineInput == '') and (inputExprStr != ''):
            if inputExprStr[0] == ']':
               self.doCommand( inputExprStr[:-1] )
            else:
               try:
                  response = self.instrumentedEval( inputExprStr )
                  inputText, retVal, console, pr_err, ev_err, cost = response
                  
                  if pr_err:
                     print(pr_err)
                  else:
                     print(console)
                  
                  print( ']] ---------------------------  Completed in: {:f} seconds.  Returned:'.format(cost) )
                  print( retVal )
                  
                  self._history.append( response )
               
               except Scanner.ParseError as ex:
                  self._exceptInfo = sys.exc_info( )
                  self.writeLn( ex.generateVerboseErrorString() )

               except EvaluationError as ex:
                  self._exceptInfo = sys.exc_info( )
                  self.writeLn( ex.args[-1] )

               except Exception as ex:
                  self._exceptInfo = sys.exc_info( )
                  self.writeLn( ex.args[-1] )

               self.writeLn( )
            
            inputExprStr = ''
            
         else:
            inputExprStr += (lineInput.strip() + '\n')

   def readAndEvalFile( self, filename, testFile=False, verbosity=0 ):
      inputText = None
      with open( filename, 'r') as file:
         inputText = file.read( )
      
      if inputText is None:
         self.writeLn( 'Unable to read file.\n' )
         return
      
      if testFile:
         print( '   Test file: {0}... '.format(filename), end='' )
         self._sessionLog_test( inputText, verbosity )
      else:
         return self._sessionLog_restore( inputText, verbosity )

   def _sessionLog_restore( self, inputText, verbosity=0 ):
      exprNum = 0
      
      implStdOut = io.StringIO()
      for exprNum,exprPackage in enumerate(self._iterLog(inputText)):
         exprStr,outputStr,retValStr = exprPackage
         if verbosity == 0:
            self._interp.eval( exprStr, stdout=implStdOut )
         else:
            exprLines = exprStr.splitlines()
            print( '\n>>> {:s}'.format(exprLines[0]) )
            for line in exprLines[1:]:
               print( '... {:s}'.format(line) )
            
            resultStr = self._interp.eval( exprStr )
            print( '\n==> ' + resultStr )
         exprNum += 1
      
      return exprNum
   
   def _sessionLog_test( self, inputText, verbosity=0 ):
      numPassed = 0
      
      if verbosity >= 3:
         print()
      
      implStdOut = io.StringIO()
      for exprNum,exprPackage in enumerate(self._iterLog(inputText)):
         exprStr,expectedOutput,expectedRetValStr = exprPackage
         resultExpr = self._interp.eval( exprStr, stdout=implStdOut )
      
         # Test stdio output
         #outputText = implStdOut.getvalue()
         #if outputText == expectedOutput:
            #outputTest_passed = True
            #outputTest_reason = 'PASSED!'
         #else:
            #outputTest_passed = False
            #outputTest_reason = 'Failed!  Output value doesn\'t equal expected value.'
      
         # Test Return Value
         if (resultExpr is None) and (expectedRetValStr is not None):
            retValTest_passed = False
            retValTest_reason = 'Failed!  Returned <Code>None</Code>; expected <i>value</i>.'
         elif (resultExpr is not None) and (expectedRetValStr is None):
            retValTest_passed = False
            retValTest_reason = 'Failed!  Returned a value; expected <Code>None</Code>'
         elif (resultExpr is not None) and (expectedRetValStr is not None):
            if resultExpr == expectedRetValStr:
               retValTest_passed = True
               retValTest_reason = 'PASSED!'
            else:
               retValTest_passed = False
               retValTest_reason = 'Failed!  Return value doesn\'t equal expected value.'
      
         # Determine Pass/Fail
         #if outputTest_passed and retValTest_passed:
         if retValTest_passed:
            test_passed = True
            test_reason = 'PASSED!'
            numPassed += 1
         else:
            test_passed = False
            test_reason = 'Failed!'
      
         if verbosity >= 3:
            print( '     {0}. {1}'.format(str(exprNum).rjust(6), test_reason) )
   
      numTests = exprNum + 1
      numFailed = numTests - numPassed
      if test_passed:
         print( 'PASSED!' )
      else:
         print( '({0}/{1}) Failed.'.format(numFailed,numTests) )
  
   def instrumentedEval( self, inputText ):
      console = io.StringIO()
      stdout  = io.StringIO()
      ev_err  = io.StringIO()
      pr_err  = io.StringIO()
      
      # Ugly Code!!!
      # The goal here is to end up with three strings after the evaluation of
      # the inputText is completed.  In one string we want everything written to
      # stdout. In the next stirng we want everything written to stderr.  In a
      # third string we want everything sent to stdout AND stderr in their
      # written order.  Hence, it would appear as the user would see written
      # to the console.  These TiedStreams create dummy stream objects that,
      # when written to, just repeat the write operation to each of the
      # underlying streams.
      
      con_out = StreamTee( console, stdout )
         # writes to both console and stdout
      
      con_evr = StreamTee( console, ev_err )
         # writes to both console and ev_err
      
      con_prr = StreamTee( console, pr_err )
         # writes to both console and pr_err
      
      try:
         retVal = None
         cost   = -1
         startTime = time.perf_counter()
         retVal = self._interp.eval( inputText, stdout=con_out, stderr=ev_err )
         endTime = time.perf_counter()
         cost = endTime - startTime
      
      except Scanner.ParseError as ex:
         self._exceptInfo = sys.exc_info( )
         print( ex.generateVerboseErrorString(), file=con_prr )

      except EvaluationError as ex:
         self._exceptInfo = sys.exc_info( )
         print( ex.args[-1], file=con_evr )

      except Exception as ex:
         self._exceptInfo = sys.exc_info( )
         print( ex.args[-1] )
         raise                                      # Should NEVER OCCUR

      con_out.flush()
      con_evr.flush()
      con_prr.flush()
      
      console.flush()
      stdout.flush()
      ev_err.flush()
      pr_err.flush()
      
      # Collect everything we know about the evaluation into a tuple.
      return Card( inputText, retVal, pr_err.getvalue(), ev_err.getvalue(), console.getvalue(), cost )

   def _iterLog( self, inputText ):
      stream = Scanner.ScannerLineStream( inputText )
      
      while True:
         # Skip empty and comment lines
         line = stream.peekLine()
         strippedLine = line.strip()
         while (strippedLine == '') or strippedLine.startswith( ';' ):
            stream.consumeLine()
            line = stream.peekLine()
            strippedLine = line.strip()
         
         if not line.startswith( '>>> ' ):
            raise Exception()
         
         # Parse Expression
         expr = line[ 4: ]
         stream.consumeLine()
         line = stream.peekLine()
         while line.startswith( '... ' ):
            expr += line[ 4: ]
            stream.consumeLine()
            line = stream.peekLine()
         
         output = None
         while not line.startswith( ('==> ','... ','>>> ') ):
            # Parse written output
            if output is None:
               output = ''
            output += line
            stream.consumeLine()
            line = stream.peekLine()
         if output:
            output = output[ : -1 ]        # remove the newline character at the end of output
         
         retVal = None
         if line.startswith( '==> ' ):
            retVal = line[ 4: ]
            stream.consumeLine()
            line = stream.peekLine()
            while not line.startswith( ('==> ','... ','>>> ') ):
               retVal += line
               stream.consumeLine()
               line = stream.peekLine()
            retVal = retVal[ : -2 ]       # remove the two newline characters at the end of retVal
         
         yield expr,output,retVal
   

   

class ScannerState( object ):
   def __init__( self ):
      self.tok               = None
      self.buffer_source     = None
      self.buffer_point      = None
      self.buffer_mark       = None
      self.buffer_lineNum    = None

class ScannerBuffer( object ):
   def __init__( self ):
      '''Initialize a scanner buffer instance.'''
      self._source  = ''   # the string to be analyzed lexically
      self._point   = 0    # the current scanner position
      self._mark    = 0    # the first character of the lexeme currently being scanned
      self._lineNum = 0    # the current line number

   def reset( self, sourceString=None ):
      '''Re-initialize the instance over a new or the current string.'''
      assert isinstance( sourceString, str ) or ( sourceString is None )

      if sourceString is None:
         self._source = ''
      else:
         self._source = sourceString

      self._point    = 0
      self._mark     = 0
      self._lineNum  = 1

   def peek( self ):
      '''Return the next character in the buffer.'''
      try:
         return self._source[ self._point ]        # raises on EOF
      except:
         return None   # Scanned past eof

   def consume( self ):
      '''Advance the point by one character in the buffer.'''
      try:
         if self._source[ self._point ] == '\n':   # raises on EOF
            self._lineNum += 1
         self._point += 1
      except:
         pass

   def consumeIf( self, aCharSet ):
      '''Consume the next character if it's in aCharSet.'''
      assert isinstance( aCharSet, str ) and (len(aCharSet) > 0)

      try:
         if self._source[ self._point ] in aCharSet:   # raises on EOF
            self.consume( )
      except:
         pass

   def consumeIfNot( self, aCharSet ):
      '''Consume the next character if it's NOT in aCharSet.'''
      assert isinstance( aCharSet, str ) and (len(aCharSet) > 0)

      try:
         if self._source[ self._point ] not in aCharSet:   # raises on EOF
            self.consume( )
      except:
         pass

   def consumePast( self, aCharSet ):
      '''Consume up to the first character NOT in aCharSet.'''
      assert isinstance( aCharSet, str ) and (len(aCharSet) > 0)

      try:
         while self._source[ self._point ] in aCharSet:   # raises on EOF
            self.consume( )
      except:
         pass

   def consumeUpTo( self, aCharSet ):
      '''Consume up to the first character in aCharSet.'''
      assert isinstance( aCharSet, str ) and (len(aCharSet) > 0)

      try:
         while self._source[ self._point ] not in aCharSet:   # raises on EOF
            self.consume( )
      except:
         pass

   def saveState( self, stateInst ):
      stateInst.buffer_source   = self._source
      stateInst.buffer_point    = self._point
      stateInst.buffer_mark     = self._mark
      stateInst.buffer_lineNum  = self._lineNum

   def restoreState( self, stateInst ):
      self._source   = stateInst.buffer_source
      self._point    = stateInst.buffer_point
      self._mark     = stateInst.buffer_mark
      self._lineNum  = stateInst.buffer_lineNum

   def markStartOfLexeme( self ):
      '''Indicate the start of a lexeme by setting the mark to the current vlaue of point.'''
      self._mark = self._point

   def getLexeme( self ):
      '''Returns the substring spanning from mark to point.'''
      return self._source[ self._mark : self._point ]

   def scanLineNum( self ):
      '''Return a tuple of ( the line num, the column num ) of point.'''
      return self._lineNum + 1

   def scanColNum( self ):
      '''Return a tuple of ( the line num, the column num ) of point.'''
      return self._point - self._linePos( ) + 1

   def scanLineTxt( self ):
      '''Return the complete text of the line currently pointed to by point.'''
      fromIdx = self._linePos( )
      toIdx   = self._source.find( '\n', fromIdx )
      if toIdx == -1:
         return self._source[ fromIdx : ]
      else:
         return self._source[ fromIdx : toIdx ]

   def _linePos( self ):
      '''Return the index into the buffer string of the first character of the current line.'''
      return self._source.rfind( '\n', self._point ) + 1

class Scanner( object ):
   def __init__( self ):
      '''Initialize a Scanner instance.'''
      self.buffer       = ScannerBuffer( )
      self._tok         = -1               # The next token

   def reset( self, sourceString=None ):
      '''Re-initialize the instance over a new or the current string.'''
      assert isinstance( sourceString, str ) or ( sourceString is None )

      self.buffer.reset( sourceString )
      self._tok         = -1
      self._states      = { }
      self.consume( )

   def peekToken( self ):
      '''Return the next (look ahead) token, but do not consume it.'''
      return self._tok

   def consume( self ):
      '''Advance the scanner to the next token/lexeme in the ScannerBuffer.'''
      self._tok = self._scanNextToken( )

   def getLexeme( self ):
      '''Return the next (look ahead) lexeme, but do not consume it.
      This should be called before consume.'''
      return self.buffer.getLexeme( )

   def saveState( self, stateInst ):
      '''Create a restore point (for backtracking).  The current
      state of the scanner is preserved under aStateName.'''
      stateInst.tok             = self._tok
      self.buffer.saveState( stateInst )

   def restoreState( self, stateInst ):
      '''Restore a saved state (backtrack to the point where the restore point was made).'''
      self._tok = stateInst.tok
      self.buffer.restoreState( stateInst )

   def tokenize( self, aString, EOFToken=0 ):
      tokenList = [ ]

      self.reset( aString )

      while self.peekToken() != EOFToken:
         token = self.peekToken()
         lex   = self.getLexeme( )
         tokenList.append( ( token, lex ) )
         self.consume( )

      tokenList.append( (EOFToken,0) )
      
      return tokenList

   def test( self, aString, EOFToken=0 ):
      '''Scanner Testing:  Print the list of tokens in the input string.'''
      try:
         tokenList = self.tokenize( aString, EOFToken )

         for tokLexPair in tokenList:
            print( '{0:<4} /{1}/'.format( *tokLexPair ) )

      except ParseError as ex:
         print( ex.errorString(verbose=True) )

      except Exception as ex:
         print( ex )

   # Contract
   def _scanNextToken( self ):
      """Consume the next token (i.e. scan past it).
      Type:          Mutator - Abstract
      Returns:       Token (actual type determined by implementation, usually an int)
      Preconditions: determined by the implementation.
      Side Effects:  Scans the next token from the source string.
      """
      raise NotImplementedError( )

class ScannerLineStream( object ):
   def __init__( self, inputText ):
      self._lines = inputText.splitlines(keepends=True)
      self._point = 0
   
   def peekLine( self ):
      try:
         return self._lines[ self._point ]
      except:
         raise StopIteration( )
   
   def consumeLine( self ):
      self._point += 1
   
   def currentLineNumber( self ):
      return self._point
   
class ParseError( Exception ):
   def __init__( self, aScanner, errorMessage, filename='' ):
      self.filename   = filename
      self.lineNum    = aScanner.buffer.scanLineNum()
      self.colNum     = aScanner.buffer.scanColNum()
      self.errorMsg   = errorMessage
      self.sourceLine = aScanner.buffer.scanLineTxt()

      self.errInfo = {
         'filename':   self.filename,
         'lineNum':    self.lineNum,
         'colNum':     self.colNum,
         'errorMsg':   self.errorMsg,
         'sourceLine': self.sourceLine
         }

   def generateVerboseErrorString( self ):
      """Generate an error string.
      Category:      Pure Function.
      Returns:       (str) A detailed textual representation of the error.
      Side Effects:  None.
      Preconditions: [AssertionError] The underlying buffer must wrap a string.
      """
      self.errInfo['indentStr'] = ' ' * ( self.errInfo['colNum'] - 1 )
      return 'Syntax Error: {filename}({lineNum},{colNum})\n{sourceLine}\n{indentStr}^ {errorMsg}'.format( **self.errInfo )

############## DEMONSTRATION #################

if __name__ == '__main__':
   class PuckScanner( Scanner ):
      # Character Sets
      WHITESPACE     = ' \t\n\r'
      SIGN           = '+-'
      DIGIT          = '0123456789'
      ALPHA_LOWER    = 'abcdefghijklmnopqrstuvwxyz'
      ALPHA_UPPER    = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
      ALPHA          = ALPHA_LOWER + ALPHA_UPPER
      SYMBOL_FIRST   = ALPHA + SIGN + '~!@#$%^&*_=\:/?<>'
      SYMBOL_REST    = SYMBOL_FIRST + DIGIT

      # Tokens
      EOF            =   0
      SYMBOL         = 101    # Value Objects
      NUMBER         = 102
      STRING         = 103
      OPEN_BRACKET   = 201    # Paired Symbols
      CLOSE_BRACKET  = 202
      SEMI_COLON     = 500    # Other Symbols
      POUND_SIGN     = 501
      PIPE           = 502

      def __init__( self, inputString='' ):
         super().__init__( inputString )

      def _scanNextToken( self ):
         self._skipWhitespaceAndComments( )

         nextChar = self.buffer.peek( )
         if nextChar is None:
            return PuckScanner.EOF
         elif nextChar == '[':
            self.buffer.markStartOfLexeme( )
            self.buffer.consume( )
            return PuckScanner.OPEN_BRACKET
         elif nextChar == ']':
            self.buffer.markStartOfLexeme( )
            self.buffer.consume( )
            return PuckScanner.CLOSE_BRACKET
         elif nextChar == ';':
            self.buffer.markStartOfLexeme( )
            self.buffer.consume( )
            return PuckScanner.SEMI_COLON
         elif nextChar == '#':
            self.buffer.markStartOfLexeme( )
            self.buffer.consume( )
            return PuckScanner.POUND_SIGN
         elif nextChar == '|':
            self.buffer.markStartOfLexeme( )
            self.buffer.consume( )
            return PuckScanner.PIPE
         elif nextChar == '"':
            return self._scanStringLiteral( )
         elif nextChar in '+-0123456789':
            return self._scanNumOrSymbol( )
         elif nextChar in PuckScanner.SYMBOL_FIRST:
            return self._scanSymbol( )
         else:
            raise ParseError( self, 'Unknown Token' )

      def _skipWhitespaceAndComments( self ):
         self.buffer.consumePast( PuckScanner.WHITESPACE )

      def _scanStringLiteral( self ):
         nextChar = self.buffer.peek( )
         if nextChar != '"':
            raise ParseError( self, '\'"\' expected.' )
         self.buffer.markStartOfLexeme( )
         self.buffer.consume( )
         self.buffer.consumeUpTo( '"' )
         lexeme = self.buffer.getLexeme( )
         self.buffer.consume( )

         return PuckScanner.STRING

      def _scanNumOrSymbol( self ):
         nextChar = self.buffer.peek( )

         self.buffer.markStartOfLexeme( )
         self.saveState( 'MY_SAVED_STATE' )          # <-------  Save the state

         self.buffer.consume( )

         if nextChar in '+-':
            secondChar = self.buffer.peek( )
            if secondChar not in '0123456789':
               self.restoreState( 'MY_SAVED_STATE' ) # <-------- Restore the state
               return self._scanSymbol( )

         self.buffer.consumePast( '0123456789' )

         if self.buffer.peek() == '.':
            # Possibly a floating point number
            self.buffer.consume()
            if self.buffer.peek() not in '0123456789':
               # Integer
               self.buffer.putBack()
               return PuckScanner.NUMBER
            else:
               self.buffer.consumePast( '0123456789' )
               return PuckScanner.NUMBER

         return PuckScanner.NUMBER

      def _scanSymbol( self ):
         self.buffer.markStartOfLexeme( )
         nextChar = self.buffer.peek()
         if nextChar not in PuckScanner.SYMBOL_FIRST:
            raise ParseError( self, 'Invalid symbol character' )
         self.buffer.consume( )
         self.buffer.consumePast( PuckScanner.SYMBOL_REST )

         return PuckScanner.SYMBOL


   puckStatements = '''
   [false member: #class] sameObjectAs: Object;
   6.83 - 3;
   "hello" length;
   5 = 5;
   true sameObjectAs: true;
   null sameObjectAs: 3;
   [false member: #class] sameObjectAs: Object;
   booleanNegation sameObjectAs: [true member: #not];
   [true member: #not] sameObjectAs: booleanNegation;
   booleanNegation sameObjectAs: [Boolean member: not];
   [Boolean member: not] sameObjectAs: booleanNegation;
   [ 1; 3; 3 + 5 ];
   myList <- #[ a; b; c ];
   myList at: 1;
   junk <- 3;
   [ 1; junk <- 0; 3 + 5 ];
   [ local <- 100; local ];
   #[ | val | val + 1 ] evalWithArgs: #[ 4 ];
   inc <- #[ | val | val + -1 ];
   inc evalWithArgs: #[ 6 ];
   #[ | val1 val2 | val1 + val2 ] evalWithArgs: #[ 1; 2 ];
   3 doTimes: #[ | x | junk <- [ junk + 1 ] ];
   ct <- 0;
   #[ ct != 3 ] whileTrue: #[ ct <- [ ct + 1 ] ];
   [ Boolean member: #not ] evalWithArgs: #[ false ];
   '''

   import cProfile

   def runTest( ):
      aPuckScanner = PuckScanner( puckStatements )
      while aPuckScanner.peekToken() != PuckScanner.EOF:
         token   = aPuckScanner.peekToken()
         lexeme  = aPuckScanner.getLexeme()
         print( '{0:03d}: /{1}/'.format( token, lexeme ) )
         aPuckScanner.consume()

      print( 'Done!' )

   cProfile.run( 'runTest()' )

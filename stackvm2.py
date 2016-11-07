#!/python3.5
import itertools
import operator as op
import math
import copy

try:
   from ltk_py3.Environment import Environment
except:
   from Environment import Environment

class INTERRUPT( Exception ):
   def __init__( self, name ):
      super().__init__( )
      self.name = name


class StackVM2( object ):
   # The VM2 Stack Machine opcodes
   #    Expect
   #    - If there's an operand, it's in register self.operand
   #    Do
   #    - Set the CP for the next instruction (+1 is guaranteed to
   #      advance to the next sequential instruction)
   
   # Examiniming run tells you everything about what the opcode should do.
   
   # Flags
   NO_ERROR              = 0
   CARRY                 = 1
   STACK_OF              = 2
   STACK_UF              = 3
   UNKNOWN_UNRECOVERABLE = 4
   BAD_ADDRESS           = 8
   HALT                  = 9
   
   def __init__( self ):
      self.CS      = None  # The Code Segment
      self.CP      = 0     # The Code Pointer
      self.IR      = ''    # Instruction Register
      
      self.SS      = [ ]   # The Stack Segment
      self.SP      = 0     # The Stack Pointer (running value for len(_SS))
      
      self.BP      = 0     # Base Pointer
      self.BINF    = None  # Base Info
      
      self.FLG     = 0     # Flag Register
      self.CT      = 0     # Instruction Counter
   
      self.ENV     = Environment( )
      self.last    = None  # Most recent result
      
      OPS          = { }       # Map:  opname -> opFn
      rOPS         = { }
      DOC          = { }
      CAT          = { }
      self.categories = CAT    # Map:  cat -> [ op, ... ]
      self.opcodes    = OPS
      self.ropcodes   = rOPS
      self.docs       = DOC
      for name in dir(StackVM2):
         if name.startswith( 'op_' ):
            fn              = getattr( self, name )
            OPS[ name[3:] ] = fn
            rOPS[ fn      ] = name[3:]
            try:
               docs = parseDoc( fn.__doc__ )
               DOC[ name[3:] ] = docs
               cat = docs[-1]
            except:
               DOC[ name[3:] ] = (name[3:],'- UNDOCUMENTED -',('',''),'','')
               cat = ''
            
            if cat not in CAT:
               CAT[ cat ] = [ name[3:] ]
            else:
               CAT[ cat ].append( name[3:] )
      
      for cat in CAT.keys():
         CAT[cat] = sorted(CAT[cat])
   
  
   def run( self, CS, env=None ):
      self.CS = CS
      self.CP = 0
      self.ENV = env
      self.FLG = 0
      OP = self.opcodes
      CS = self.CS
      CP = self.CP
      
      while True:
         try:
            while True:
               # <  --  Decode  --  >| |< -- Fetch -- >|
               opcode,self.operand =    self.CS[self.CP]
               opcode() # <-- Execute
            
         except INTERRUPT as IRQ:
            if IRQ.name == 'HALT':
               self.last = self.SS[-1]
               return self.last
            else:
               raise
  
   def iterrun( self, CS, env=None ):
      self.CS = CS
      self.CP = 0
      self.ENV = env
      self.FLG = StackVM.NO_ERROR
      OP = self.opcodes
      CS = self.CS
      
      while True:
         try:
            while True:
               yield self
               opcode,self.operand = self.CS[self.CP]
               opcode()
         except INTERRUPT as IRQ:
            if IRQ.name == 'HALT':
               self.last = self.SS[-1]
               raise StopIteration()
            else:
               raise

   # #######
   # PROBES & OPCODE implementation tools
   def _trace( self, instructionNum, hexintegers=False ):
      if hexintegers:
         print( '{:012X}:{:06X}:  {:22s} || {:s}'.format( instructionNum, self.CP, self._trace_instruction(hexintegers=hexintegers), self._trace_stack(40,hexintegers=hexintegers) ) )
      else:
         print( '{:012d}:{:06d}:  {:22s} || {:s}'.format( instructionNum, self.CP, self._trace_instruction(), self._trace_stack(40) ) )
 
   def _trace_instruction( self, hexintegers=False ):
      opcode = self.CS[ self.CP ]
      if isinstance( opcode, tuple ):
         try:
            opcode,operand = opcode
            if isinstance( operand, list ):
               operand = '[...]'
         except:
            opcode = opcode[0]
            operand = ''
         return '{0:10s}  {1:10s}'.format(opcode,str(operand))
      
      # Disassemble the Current Instruction
      operandList = [ ]
      for operand in self.CS[self.CP + 1 : ]:
         if isinstance( operand, int ) and hexintegers:
            operandList.append( hex(operand).upper() )
         elif isinstance( operand, (int,float,bool) ):
            operandList.append( str(operand) )
         elif isinstance( operand, str ):
            if operand in self.opcodes:
               break
            else:
               operandList.append( operand[:12] )
         elif isinstance( operand, list ):
            operandList.append( '[...]' )
         elif isinstance( operand, tuple ):
            operandList.append( '(...)' )
         else:
            raise Exception( )
      
      operandListStr = ', '.join( operandList ).rstrip()
      result = '{0:10s}  {1:10s}'.format(opcode,operandListStr)
      return result

   def _trace_stack( self, fieldSize=50, hexintegers=False ):
      return str(self.SS)[-fieldSize:].rjust(fieldSize)
   
   def doc_instructionSet( self ):
      CAT = self.categories
      DOC = self.docs
      for cat in sorted(CAT.keys()):
         print( 'CATEGORY: {:s}'.format(cat) )
         print( '----------' + ('-' * len(cat)) )
         
         for opName in CAT[cat]:
            op,usage,stack,descr,cat = DOC[opName]
            print( 'Instruction:  {:s}'.format(usage))
            print( '      Stack:  {:s}  ->  {:s}'.format(*stack))
            print( '      Note:   {:s}'.format(descr))

   def top( self, num ):
      return self.SS[ 0 - num : ]

   def IDENTITY( self, arg ):
      return arg
   
   def UNARY_OP( self, type1, fn ):
      self.SS[ -1 ] = fn( type1(self.SS[-1]) )
      self.CP += 1
   
   def BINARY_OP( self, fn, type1, type2 ):
      arg2 = self.SS.pop( )
      self.SS[-1] = fn( type1(self.SS[-1]), type2(arg2) )
      self.CP += 1
   
   #def BINARY_OP( self, fn, type1, type2 ):
      # Weakly Typed Version
      #self.SS[-1] = (lambda x: self.SS[-1]   +   x)(self.SS.pop())
      #self.CP += 1
      
      # Strongly Typed Version
      #self.SS[-1] = (lambda x: type1(self.SS[-1])   +   type2(x))(self.SS.pop())
      #self.CP += 1
   
   def BINARY_OP2( self, fn, type1, type2 ):
      '''Same as above but swapps the args to fn()'''
      self.SS[-1] = fn( type2(self.SS.POP()), type1(self.SS[-1]) )
      self.CP += 1
   
   #def BINARY_OP2( self, fn, type1, type2 ):
      #self.SS[-1] = (lambda x: x   +   self.SS[-1])(self.SS.pop())
      #self.CP += 1
   
   def CJUMP_OP( self, address, fn ):
      arg1 = self.SS.pop( )
      if fn(arg1):
         self.CP = address
      else:
         self.CP += 1
   
   # #######
   # OPCODES
   
   # patterns
   # - to get the top n items:
   #     arg1, arg2 = self._SS[ -2 : ]
   # - to replace stack top (push without popping)
   #     self._[ -1 ] = val
   # - to get an operand (which follows an opcode)
   #  operand = self._CS[ self._CP + 1 ]    # get operand
   
   # Stack Operations
   def op_PUSH( self ):
      '''PUSH <value>
      SS:  [ ... ]  ->  [ ..., <value> ]
      :    Push a value onto the stack.
      #STACK
      '''
      self.SS.append( self.operand )
      self.CP += 1
   
   def op_POP( selfone ):                      # POP <count>
      '''POP
      SS:  [ ..., <top> ]  ->  [ ... ]
      :    Remove and discard one item from the top of the stack.
      #STACK
      '''
      self.SS.pop( )
      self.CP += 1
   
   def op_POPn( self ):                     # POPn <count>
      '''POP <count>
      SS:  [ ... ]  ->  [ ... ]
      :    Remove and discard <count> items from the top of the stack
      #STACK
      '''
      count = self.operand
      del self.SS[ 0 - count : ]
      self.CP += 1

   def op_TOPSET( self, value ):                   # TOPSET <val>
      '''TOPSET <value>
      SS:  [ ..., <oldTop> ]  ->  [ ..., <value> ]
      :    Replace the stack's top item with <value>.
      #STACK
      '''
      self.SS[ -1 ] = self.operand
      self.CP += 1
   
   def op_PUSH_NTH( self, offset ):
      '''PUSH_NTH <offset>
      SS:  [ ... ]  ->  [ ..., <nthItem>
      :    Push the nth (-1, -2, etc.) offset from the stack top.
      #STACK
      '''
      self.SS.append( self.SS[ 0 - offset ] )      
      self.CP += 1

   def op_SWAPXY( self):
      '''SWAPXY
      SS:  [ ..., <x>, <y> ]  ->  [ ..., <y>, <x> ]
      :    Swap the two top stack items.
      #STACK
      '''
      self.SS[ 0 - 2 ], self.SS[ 0 - 1 ] = self.SS[ 0 - 2 : ]
      self.CP += 1

   # Environment Management
   def op_BIND( self):
      '''BIND
      SS:  [ ..., <value>, <symbol> ]  ->  [ ..., <value> ]
      :    Bind a symbold to a value in the local namespace.
      #ENVIRONMENT
      '''
      value = self.SS.pop( )
      name  = self.SS[-1]
      self.ENV.declLocal( value, name )
      self.CP += 1
   
   def op_BINDG( self):
      '''BINDG
      SS:  [ ..., <value>, <symbol> ]  ->  [ ..., <value> ]
      :    Bind a symbol to a value in the global namespace.
      #ENVIRONMENT
      '''
      name = self.SS.pop( )
      obj  = self.SS[-1]
      self.ENV.declGlobal( name, obj )
      self.CP += 1
   
   def op_UNBIND( self):
      '''UNBIND
      SS:  [ ..., <symbol> ]  ->  [ ... ]
      :    Remove any bindings to the symbol.
      #ENVIRONMENT
      '''
      name = self.SS.pop()
      self.ENV.unDecl( name )
      self.CP += 1

   def op_REBIND( self):
      '''BIND
      SS:  [ ..., <value>, <symbol> ]  ->  [ ..., <value> ]
      :    Rebind a symbol to a new value.
      #ENVIRONMENT
      '''
      name = self.SS.pop( )
      obj  = self.SS[ -1 ]
      self.ENV.rebind( name, obj )
      self.CP += 1
   
   def op_DEREF( self):
      '''DEREF
      SS:  [ ..., <symbol> ]  ->  [ ..., <value> ]
      :    Get value to which a symbol is bound.
      :    If <symbol> is not bound, <value> will be <symbol>
      #ENVIRONMENT
      '''
      name = self.SS[-1]
      self.SS[-1] = self.ENV.get( name )
      self.CP += 1
   
   def op_BEGIN( self):
      '''BEGIN
      :    Begin/Open a new nested lexical scope in the environment.
      #ENVIRONMENT
      '''
      self.ENV = Environment( self.ENV )
      self.CP += 1
   
   def op_END( self):
      '''END
      :    End/Close the current nested lexical scope in the environment.
      #ENVIRONMENT
      '''
      self.ENV = self.ENV.parentEnv( )
      self.CP += 1

   # Register Controls
   def op_PUSH_CS( self):
      '''PUSH_CS
      SS:  [ ... ]  ->  [ ..., <saved CS> ]
      :    Push a copy of CS onto the stack.
      #REGISTERS
      '''
      self.SS.append( self.CS )
      self.CP += 1
   
   def op_POP_CS( self):
      '''POP_CS
      SS:  [ ..., <saved CS> ]  ->  [ ... ]
      :    Pop the top of the stack, placing the popped value into CS.
      #REGISTERS
      '''
      self.CS = self.SS.pop( )
      self.CP += 1

   def op_PUSH_FLG( self):
      '''PUSH_FLG
      SS:  [ ... ]  ->  [ ..., <saved FLG> ]
      :    Push a copy of FLG onto the stack.
      #REGISTERS
      '''
      self.SS.append( self.FLG )
      self.CP += 1

   def op_POP_FLG( self):
      '''POP_FLG
      SS:  [ ..., <saved FLG> ]  ->  [ ... ]
      :    Pop the top of the stack, placing the popped value into FLG.
      #REGISTERS
      '''
      self.FLG = self.SS.pop( )
      self.CP += 1

   # Subroutine
   def op_CALL( self):
      '''CALL <numArgs>
      SS:  [ ..., <argn>, ..., <arg2>, <arg1>, <newCodeSeg> ]  -> [ ..., <argn>, ..., <arg2>, <arg1> ]
      :    Call the <newCodeSeg>.
      #CALL
      '''
      # Prepare new Stack Frame & Return Info
      numArgs    = self.operand
      newCodeSeg = self.SS.pop( )
      
      # Save current stack frame
      self.SP    = len(self.SS)     # SP set to stack top
      
      ret_SP = self.SP - numArgs
      ret_BP = self.BP
      ret_CS = self.CS
      ret_CP = self.CP + 1
      ret_op = self.operand
      
      self.BINF  = [ret_op, ret_CS, ret_CP, ret_SP, ret_BP, self.BINF]
      
      # Construct new stack frame
      self.BP    = self.SP             # BP points to argument 0
      self.CS    = newCodeSeg
      self.CP    = 0
   
   def op_RET( self):
      '''RET
      SS:  [ ..., <stack frame>, <return value> ]  ->  [ ..., <return value> ]
      :    Restore the prior stack frame being sure to preserve the return value.
      #CALL
      '''
      returnValue = self.SS.pop( )     # Save a copy of the return value
      self.operand,self.CS,self.CP,self.SP,self.BP,self.BINF = self.BINF # Restore the caller's stack frame
      del self.SS[ self.SP : ]         # Pop all of the caller's arguments
      self.SS.append( returnValue )    # Restore the return value to the top of the stack
   
   def op_RETv( self ):
      '''RET <return value>
      SS:  [ ..., <old stack frame>, <current stack frame> ]  ->  [ ..., <old stack frame>, <return value> ]
      :    Restore the prior stack frame being sure to preserve the return value.
      #CALL
      '''
      returnValue = self.SS.operand
      self.CS, self.CP, self.SP, self.BP, self.BINF = self.BINF # Restore the caller's stack frame
      del self.SS[ self.SP : ]         # Pop all of the caller's arguments
      self.SS.append( returnValue )    # Restore the return value to the top of the stack
   
   def op_PUSH_BPOFF( self):
      '''PUSH_BPOFF <offest>
      SS:  [ ... ]  ->  [ ..., <value> ]
      :    Push the item at the indicated offset from the Base Pointer.
      :    e.g. -1 pushes the stack item at stack index [BP + <offset>],
      :    which is the first arguemnt to the current stack frame.
      #CALL
      '''
      self.SS.append( self.SS[self.BP + self.operand] )   # operand = offset
      self.CP += 1

   def op_CALLp( self):
      '''CALLP <numArgs>
      SS:  [ ..., <python function> ]  ->  [ ... ]
      :    Call the python function.  If it succeeds the args will be replaced
           by the return value of the python function.  If it fails, the FLG
           register will be set to UNKNOWN_UNRECOVERABLE and the stack will be
           identical to how it was before the call.
      #CALLP
      '''
      numArgs = self.operand
      pyFn    = self.SS.pop()
      
      # Retrieve the dynamic arguments
      try:
         args = self.SS[ 0 - numArgs : ]
      except:
         self.FLG = self.UNKNOWN_UNRECOVERABLE
         return
      
      # Delete the dynamic arguments
      del self.SS[ 0 - numArgs : ]
      
      # Call the Python function
      try:
         result  = pyFn( self, *args )
      except:
         self.SS.extend( args )   # restore the original stack
         self.FLG = self.UNKNOWN_UNRECOVERABLE
         return
      
      # push the return value
      self.SS.append( result )
      
      self.CP += 1

   # Basic Branching
   def op_HALT( self):
      '''HALT
      : Terminate the current process.
      #BRANCH'''
      raise INTERRUPT( 'HALT' )

   def op_JMP( self):
      '''JMP <address>
      :    Set the CP to <address>.
      #BRANCH
      '''
      self.CP = self.operand

   def op_JMP_T( self):
      '''JMP_T <address>
      SS:  [ ..., <value> ]  ->  [ ... ]
      :    Set the CP to <address>, if <value> is true.
      #BRANCH
      '''
      if self.SS.pop() == True:
         self.CP = self.operand
      else:
         self.CP += 1

   def op_JMP_F( self):
      '''JMP_F <address>
      SS:  [ ..., <value> ]  ->  [ ... ]
      :    Set the CP to <address>, if <value> is false.
      #BRANCH
      '''
      if self.SS.pop() == False:
         self.CP = self.operand
      else:
         self.CP += 1

   # Boolean Operations
   def op_bNOT( self):
      '''bNOT
      SS:  [ ..., <value> ]  ->  [ ..., (boolean-not <value>) ]
      :    Unary-op; pop 1 arg, compute boolean-not from popped args, push result.
      #ALU.BOOLEAN
      '''
      self.BINARY_OP( op.not_, bool )

   def op_bAND( self):
      '''bAND
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> boolean-AND <value2>) ]
      :    Binary-op; pop 2 args, compute boolean-and from popped args, push result.
      #ALU.BOOLEAN
      '''
      self.BINARY_OP( lambda x,y: x and y, bool, bool )

   def op_bOR( self):
      '''bOR
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> boolean-OR <value2>) ]
      :    Binary-op; pop 2 args, compute boolean-or from popped args, push result.
      #ALU.BOOLEAN
      '''
      self.BINARY_OP( lambda x,y: x or y, bool, bool )

   # Integer Oprations
   def op_iABS( self):
      '''iABS
      SS:  [ ..., <value> ]  ->  [ ..., (absolute-value <value>) ]
      :    Unary-op; pop 1 arg, compute absolute value from popped args, push result.
      #ALU.INTEGER
      '''
      self.UNARY_OP( abs, int )

   def op_iCHSIGN( self):
      '''iCHSIGN
      SS:  [ ..., <value> ]  ->  [ ..., (-1 * <value>) ]
      :    Unary-op; pop 1 arg, compute numerical negation from popped args, push result.
      #ALU.INTEGER
      '''
      self.UNARY_OP( op.neg, int )

   def op_iPROMOTE( self): # int -> float
      '''iPROMOTE
      SS:  [ ..., <value> ]  ->  [ ..., (convert-to-float <value>) ]
      :    Unary-op; pop 1 arg, compute floating pointer equivalent, push result.
      #ALU.INTEGER
      '''
      self.UNARY_OP( float, int )

   def op_iEQ( self):
      '''iEQ
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> == <value2>) ]
      :    Binary-op; pop 2 args; compute integer equality; push bolean result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.__eq__, int, int )
   
   def op_iNE( self):
      '''iNE
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> != <value2>) ]
      :    Binary-op; pop 2 args; compute integer inequality; push bolean result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.__ne__, int, int )
   
   def op_iGT( self):
      '''iGT
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> > <value2>) ]
      :    Binary-op; pop 2 args; compute integer inequality; push result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.__gt__, int, int )
   
   def op_iGE( self):
      '''iGE
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> >= <value2>) ]
      :    Binary-op; pop 2 args; compute integer inequality; push bolean result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.__ge__, int, int )
   
   def op_iLT( self):
      '''iLT
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> < <value2>) ]
      :    Binary-op; pop 2 args; compute integer inequality; push bolean result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.__lt__, int, int )
   
   def op_iLE( self):
      '''iLE
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> <= <value2>) ]
      :    Binary-op; pop 2 args; compute integer inequality; push bolean result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.__le__, int, int )
   
   def op_iINC( self):
      '''iINC
      SS:  [ ..., <value> ]  ->  [ ..., (<value> + 1) ]
      :    Unary-op; pop 1 arg; compute integer increment; push result.
      #ALU.INTEGER
      '''
      self.UNARY_OP( lambda x: x + 1, int )
   
   def op_iDEC( self):
      '''iDEC
      SS:  [ ..., <value> ]  ->  [ ..., (<value> - 1) ]
      :    Unary-op; pop 1 arg; compute integer decrement; push result.
      #ALU.INTEGER
      '''
      self.UNARY_OP( lambda x: x - 1, int )

   def op_iADD( self):
      '''iADD
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> + <value2>) ]
      :    Binary-op; pop 2 args; compute integer sum; push result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.add, int, int )

   def op_iSUB( self):
      '''iSUB
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> - <value2>) ]
      :    Binary-op; pop 2 args; compute integer difference; push result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.sub, int, int )

   def op_iMUL( self):   
      '''iMUL
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> * <value2>) ]
      :    Binary-op; pop 2 args; compute integer product; push result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.mul, int, int )

   def op_iDIV( self):
      '''iMUL
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> / <value2>) ]
      :    Binary-op; pop 2 args; compute integer ratio; push result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.floordiv, int, int )
   
   def op_iMOD( self):
      '''iMUL
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> modulo <value2>) ]
      :    Binary-op; pop 2 args; compute integer remainder; push result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.mod, int, int )
   
   # List Operations
   def op_lPACK( self):       # [ obj1, obj2, ... objCount ]  =>  [ ..., [obj1, obj2, ...] ]
      count  = self.SS.pop( )
      values = self.SS[ 0 - count : ]
      del self.SS[ 0 - count - 1 : ]
      self.SS.append( values )
      self.CP += 1
   
   def op_lUNPACK( self):     # [ list ] <- SP   =>   [ list-contents ] <- SP
      values = self.SS.pop( )
      count  = len(values)
      values.append( count )
      self.SS.extend( values )
      self.CP += 1
   
   def op_lREVERSE( self):    # [ ..., list ]  =>  [ ..., reversed(list) ]
      theList = self.SS[-1].reverse()
      self.CP += 1

   def op_lLEN( self):        # [ ..., list ]  =>  [ ..., len(list) ]
      theList = self.SS[ -1 ]
      self.SS[-1] = len(theList)
      self.CP += 1

   def op_lAT( self):         # [ list, list-index ] <- SP  =>  [ list, list-item ]
      index = self.SS[ -1 ]
      aList = self.SS[ -2 ]
      self.SS[ -1 ] = aList[ index ]
      self.CP += 1
   
   def op_lATSET( self):      # [ list, list-index, newValue ]  ;; modify list at list-index with newValue
      newValue = self.SS.pop( )
      index    = self.SS.pop( )
      theList  = self.SS[ -1 ]
      theList[ index ] = newValue
      self.CP += 1
   
   def op_lPUSH( self):       # [ list, newItem ]
      newItem  = self.SS.pop( )
      theList  = self.SS[ -1 ]
      theList.push( newItem )
      self.CP += 1
   
   def op_lPOP( self):        # [ list ]  =>  [ oldListTop ]
      theList  = self.SS[ -1 ]
      value    = theList.pop( )
      self.SS.append( value )
      self.CP += 1
   
   def op_lCAT( self):        # [ list1, list2 ]  => [ <list-1-contents> <list-2-contents> ]
      list2 = self.SS.pop()
      list1 = self.SS[ -1 ]
      self.SS[ -1 ] = list1 + list2
      self.CP += 1
   
   def op_lSPLIT( self):      # [ ..., aList, size ]  =>  [ ..., aList[ : size ], aList[ size : ] ]
      count = self.SS.pop( )
      theList = self.SS[ -1 ]
      self.SS[ -1 ] = theList[ : count ]
      self.SS.append( theList[ count : ] )
      self.CP += 1

   def op_lCOPY( self):
      top = self.SS[ -1 ]
      top = copy.copy( top )
      self.SS.push( top )
      self.CP += 1
   
   def op_lSWAPSTACK( self):  # [ ..., stack-A ] => [ ..., oldStack ]
      '''SWAPSTACK
      SS = currentStack           SS = alternateStack
      [..., alternateStack ]  =>  [ ..., currentStack ]
      '''
      newStack = self.SS.pop( )
      oldStack = self.SS
      self.SS = newStack
      newStack.push( oldStack )
      self.CP += 1
   
   def op_lPUSHNEWLIST( self):      # push a new empty list onto the stack.
      self.SS.push( list() )
      self.CP += 1


      
def dissassemble( codeSeg, opcodes, hexintegers=False ):
   CS      = codeSeg
   opcodes = [ code.upper() for code in opcodes ]
   lines   = [ ]

   address = 0
   tok     = CS[address]
   try:
      while tok.upper() in opcodes:
         newLine = [ address, tok ]
         lines.append( newLine )
         address += 1
         tok = CS[address]
         while (not isinstance(tok,str)) or (tok.upper() not in opcodes):
            newLine.append( tok )
            address += 1
            tok = CS[address]
   except IndexError:
      pass
   
   for addr, opCode, *args in lines:
      if hexintegers:
         argStrs = [ hex(val).upper() if isinstance(val,int) else str(val) for val in args ]
      else:
         argStrs = [ str(val) for val in args ]
      
      try:
         argStr = ', '.join(argStrs)
      except:
         argStr = ''
   
      if hexintegers:
         print( '{:x6X}: {:10s}   {:22s}'.format(addr, opCode, argStr) )
      else:
         print( '{:06d}: {:10s}   {:22s}'.format(addr, opCode, argStr) )

import functools
class CodeObject2( object ):
   def __init__( self, opCodeMap, src=None, opt=None, obj=None, exe=None, labels=None, refs=None ):
      self.opCodeMap = opCodeMap
      self.set( src,opt,obj,exe,labels,refs )
   
   def set( self, src=None, opt=None, obj=None, exe=None, labels=None, refs=None ):
      if src is None:
         src = ''
      
      if opt is None:
         opt = [ ]
      
      if obj is None:
         obj = [ ]
      
      if exe is None:
         exe = [ ]
      
      if labels is None:
         labels = { }
      
      if refs is None:
         refs = { }
      
      # Source Code Support
      self.sourceCode     = src
      
      # Optimized Source Code Support
      self.optimizedCode  = opt
      
      # Assembled Object Code Support
      self.objectCode     = obj
      self.staticLabels   = labels
      self.staticRefs     = refs
      
      # Executable Code Support
      self.executableCode = exe

   def optimize( self ):  # src -> opt
      # Clear generated objects.
      # If assembly fails for some reason these will still be valid
      self.optimizedCode  = [ ]
      self.objectCode     = [ ]
      self.executableCode = [ ]
      self.staticLabels   = { }
      self.staticRefs     = { } 
      
      # Temporaries to hold the optimized code
      optimizedCode       = [ ]
      
      # Main Optimization Loop
      opt = Optimizer()
      self.optimizedCode = opt.optimize( self.sourceCode )
   
      # If optimization didn't fail, reassign
      self.optimizedCode  = optimizedCode
   
   def assemble( self ):  # src|opt -> obj
      # Clear generated objects.
      # If assembly fails for some reason these will still be valid
      self.objectCode     = [ ]
      self.executableCode = [ ]
      self.staticLabels   = { }
      self.staticRefs     = { } 
      
      # Temporaries to hold the generated code
      objectCode          = [ ]
      staticLabels        = { }     # Map:  label:str -> address
      staticRefs          = { }     # Map:  label:str -> [ <reference offset> ]
      
      if len(self.optimizedCode) > 0:
         source = self.optimizedCode
      else:
         source = self.sourceCode
   
      # Assembly Main Loop
      address = 0
      for line in source:
         # Parse the instruction line
         label    = None
         opcode   = line[0]
         operands = line[1:]
         if isinstance( opcode, str ) and (opcode[-1] == ':'):
            label    = line[0]
            opcode   = line[1]
            operands = line[2:]
      
         # Decode the instruction line
         if label:
            staticLabels[label] = address
      
         # Record Static Value References
         for argNum,operand in enumerate(operands):
            if isinstance(operand, str):
               if operand not in staticRefs:
                  staticRefs[ operand ] = [ ]
               staticRefs[ operand ].append( (address,argNum) )
      
         # Add assembled instruction
         if len(operands) == 0:
            objectCode.append( (opcode,None) )
         else:
            objectCode.append( (opcode,*operands) )
      
         address += 1
      
      # If assembly didn't fail, we can reassign
      self.objectCode     = objectCode
      self.staticLabels   = staticLabels
      self.staticRefs     = staticRefs
   
   def link( self ):      # obj -> exe
      # Clear generated objects.
      # If linking fails for some reason these will still be valid
      self.executableCode = [ ]
      
      # Temporaries to hold the generated code
      exe = self.objectCode[:]
      
      # Linker Main Loop
      for label,refList in self.staticRefs.items():
         try:
            address = self.staticLabels[label]
            for refAddr,refArg in refList:
               exe[refAddr] = ( exe[refAddr][0], address )
         except:
            pass
      
      # If linking didn't fail we can reassign
      self.executableCode = exe
   
   @staticmethod
   def frozenCall( opCodeMap, opcode, arg ):
      op = opCodeMap[opcode]
      def fn( ):
         op( arg )
      return fn
      #return lambda x=arg: op(x)
   
   def partialize( self ):
      newExe = [ ]
      
      for opcode,*operands in self.executableCode:
         #ptfn = CodeObject.frozenCall( self.opCodeMap, opcode, *operands )
         #newExe.append( ptfn )
         ptFn = self.opCodeMap[opcode]
         newExe.append( (ptFn, *operands) )
      
      self.executableCode = newExe
   
   def pipeline( self, address, sentinel=('HALT', 'JMP*', 'CALL*', 'RET') ):
      pass
   
   def __getitem__( self, address ):
      return self.executableCode[ address ]

   def dissassemble( self, which='exe' ):
      if which in ( 'src','opt' ):
         if (which == 'src') and isinstance( self.sourceCode, str ):
            return self.sourceCode
         
         toDis = self.sourceCode if which == 'src' else self.optimizedCode
         return self._dis_src( toDis )
      
      if which == 'obj':
         if len(self.optimizedCode) > 0:
            return dissassemble( which='opt' )
         elif len(self.sourceCode) > 0:
            return dissassemble( which='src' )
         else:
            return self._dis_src( self.objectCode )
      
      if which == 'exe':
         if len(self.optimizedCode) > 0:
            return dissassemble( which='opt' )
         elif len(self.sourceCode) > 0:
            return dissassemble( which='src' )
         else:
            return self._dis_exe()
      
      raise NotImplemented()
   
   def _dis_src( self, aSrc ):
      raise NotImplemented()
      

   def _dis_exe_( self ):
      raise NotImplemented()      

class Optimizer( object ):
   def __init__( self ):
      self._stack = [ ]
      self._opts  = { }
   
   def stack( self ):
      return self._stack

   def optimize( self, source, **flags ):
      src = source[:]
      defaultFlags = { stk:True for stk in self._stack }
      defaultFlags.update( flags )
      
      for optName in self._stack:
         if defaultFlags[optName]:
            opt = self._opts[optName]
            opt.optimize(src)
      
      return src

class PeepholeOptimizer( object ):
   def __init__( self ):
      pass
   
   def optimize( self, source, **flags ):
      pass

if __name__ == '__main__':
   vm = StackVM2( )
   fib = CodeObject2( vm.opcodes, src=[               # [ ..., arg ]
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH',                  2 ],
      [                  'iCMP'                     ],
      [                  'JMP_GT',          'else:' ],
      [                  'PUSH',                  1 ],
      [                  'RET'                      ],
      [ 'else:',         'PUSH_BPOFF',           -1 ],
      [                  'iDEC'                     ],
      [                  'PUSH_CS'                  ],
      [                  'CALL',                  1 ],   # Recursive call
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH',                  2 ],
      [                  'iSUB'                     ],
      [                  'PUSH_CS'                  ],
      [                  'CALL',                  1 ],   # Recursive call
      [                  'iADD'                     ],
      [ 'end:',          'RET'                      ]
   ] )
   fib.assemble( )
   fib.link( )
   fib.partialize( )

   dbl = CodeObject2( vm.opcodes, src=[
      [                  'PUSH_BPOFF',            0 ],
      [                  'PUSH',                  2 ],
      [                  'iMUL'                     ],
      [                  'RET'                      ]
   ] )
   dbl.assemble( )
   dbl.link( )
   
   sqr = CodeObject2( vm.opcodes, src=[
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH_BPOFF',           -1 ],
      [                  'iMUL'                     ],
      [                  'RET'                      ]
   ] )
   sqr.assemble( )
   sqr.link( )
   
   '''
   def fact( n ):
      if n == 0:
         return 1
      else:
         return n * fact(n - 1)
   '''
   fct = CodeObject2( vm.opcodes, src=[
      [                  'PUSH_BPOFF',            0 ],
      [                  'PUSH',                  0 ],
      [                  'iCMP'                     ],
      [                  'JMP_NE',          'else:' ],
      [                  'PUSH',                  1 ],
      [                  'JMP',             'end:'  ],
      [ 'else:',         'PUSH_BPOFF',            0 ],
      [                  'PUSH_BPOFF',            0 ],
      [                  'iDEC'                     ],
      [                  'PUSH_CS'                  ],
      [                  'CALL',                  1 ],
      [                  'iMUL'                     ],
      [ 'end:',          'RETY'                     ]
   ] )
   fct.assemble( )
   fct.link( )
   
   prog = CodeObject2( vm.opcodes, src=[
      [                  'PUSH',                  25 ],
      [                  'PUSH',  fib.executableCode ],   # push the function
      [                  'CALL',                   1 ],   # call the function
      [                  'HALT'                      ]
   ] )
   prog.assemble( )
   prog.link( )
   prog.partialize( )
   
   from util_profile import PerfTimer
   
   entryPoint = prog.executableCode
   
   intructionCount = 0
   with PerfTimer( ):
      vm.run( entryPoint )   
      #instructionCount = vm.run_withTrace( entryPoint )

   print( vm.SS.pop() )
   PerfTimer.dump( )
   #if instructionCount > 0:
      #print( 'Number of vm instructions executed: {:d}.'.format(instructionCount))
   
   
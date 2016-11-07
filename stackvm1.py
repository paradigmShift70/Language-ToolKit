#!python3.5

import itertools
import operator as op
import math
import copy

try:
   from Environment import Environment
except:
   from ltk_py3.Environment import Environment

class INTERRUPT( Exception ):
   def __init__( self, name ):
      super().__init__( )
      self.name = name

   
class StackVM( object ):
   # The VM1 Stack Machine opcodes
   #    Expect
   #    - If there's an operand, it's = self.CS[self.CP+1]
   #    Do
   #    - Set the CP for the next instruction. If this operand has no
   #      operand, then the usual next instruction = self.CS[self.CP+1].
   #      However, if this instruction has an operand then CP+1 is the location
   #      of this instructions operand therfor the usual next instruction
   #      = self.CS[self.CP+2]
   
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
      DOC          = { }
      CAT          = { }
      self.categories = CAT    # Map:  cat -> [ op, ... ]
      self.opcodes    = OPS
      self.docs       = DOC
      for name in dir(StackVM1):
         if name.startswith( 'op_' ):
            fn              = getattr( self, name )
            OPS[ name[3:] ] = fn
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
   
  
   def _run_( self, CS, env=None ):
      self.CS = CS
      self.CP = 0
      self.ENV = env
      self.FLG = 0
      OP = self.opcodes
      CS = self.CS
      
      while True:
         while self.FLG == 0:
            fetch()
            decode()
            execute()
      
         if self.FLG == HALT:
            return stack[-1]
         else:
            pass
  
   def loadLink( self, aCodeSeg ):
      OP = self.opcodes
      return [ OP.get(elt,elt) for elt in aCodeSeg ]

   def reloadLib( self, anEnv=None ):
      if anEnv is None:
         anEnv = self.ENV
      
      gl = anEnv._global()._locals
      reLinkedLocals = { }
      for name,val in gl.items():
         if isinstance( val, list ):
            reLinkedLocals[name] = self.loadLink(val)
      
      anEnv._global()._locals.update( reLinkedLocals )

   def ll_run( self, CS, env=None ):
      self.CS = CS
      self.CP = 0
      self.ENV = env
      self.FLG = 0
      OP = self.opcodes
      CS = self.CS
      
      newCS = [ OP.get(elt,elt) for elt in CS ]
      self.CS = newCS
      
      while True:
         try:
            while True:
               self.CP = self.CS[self.CP]()
               #func = self.CS[ self.CP ]
               #func( )
         except INTERRUPT as IRQ:
            if IRQ.name == 'HALT':
               self.last = self.SS[-1]
               return self.last
            else:
               raise
         except:
            pass
  
   def run( self, CS, env=None ):
      self.CS = CS
      self.CP = 0
      self.ENV = env
      self.FLG = 0
      OP = self.opcodes
      CS = self.CS
      
      while True:
         try:
            while True:
               OP[self.CS[self.CP]]( )
               #self.IR = self.CS[ self.CP ]
               #self.IR( )
         except INTERRUPT as IRQ:
            if IRQ.name == 'HALT':
               self.last = self.SS[-1]
               return self.last
            else:
               raise
  
   def run_p( self, CS, env=None ):
      self.CS = CS
      self.CP = 0
      self.ENV = env
      self.FLG = 0
      OP = self.opcodes
      CS = self.CS
      
      while True:
         try:
            while True:
               #OP[self.CS[self.CP]]( )
               self.CS[self.CP]( )
               #self.IR = self.CS[ self.CP ]
               #self.IR( )
         except INTERRUPT as IRQ:
            if IRQ.name == 'HALT':
               self.last = self.SS[-1]
               return self.last
            else:
               raise
  
   def run_q( self, CS, env=None ):
      self.CS = CS
      self.CP = 0
      self.ENV = env
      self.FLG = 0
      OP = self.opcodes
      CS = self.CS
      
      while True:
         try:
            while True:
               #OP[self.CS[self.CP]]( )
               pass #CP = CS[CP]( )self.CS[self.CP]( )
               #self.IR = self.CS[ self.CP ]
               #self.IR( )
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
               OP[ self.CS[self.CP] ]( )
         except INTERRUPT as IRQ:
            if IRQ.name == 'HALT':
               self.last = self.SS[-1]
               raise StopIteration()
            else:
               raise

   def run_co( self, aCodeObj ):
      pass

   # #######
   # PROBES & OPCODE implementation tools
   def _trace( self, instructionNum, hexintegers=False ):
      if hexintegers:
         print( '{:012X}:{:06X}:  {:22s} || {:s}'.format( instructionNum, self.CP, self._trace_instruction(hexintegers=hexintegers), self._trace_stack(40,hexintegers=hexintegers) ) )
      else:
         print( '{:012d}:{:06d}:  {:22s} || {:s}'.format( instructionNum, self.CP, self._trace_instruction(), self._trace_stack(40) ) )
 
   def _trace_instruction( self, hexintegers=False ):
      opcode = self.CS[ self.CP ]
      
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
      result = '{0:10s}  {1:10}'.format(opcode,operandListStr)
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
      #arg1 = self.SS[ -1 ]
      self.SS[ -1 ] = fn( type1(self.SS[-1]) )
      self.CP += 1
   
   def BINARY_OP( self, fn, type1, type2 ):
      arg2 = self.SS.pop( )
      #arg1 = self.SS[ -1 ]
      self.SS[ -1 ] = fn( type1(self.SS[-1]), type2(arg2) )
      self.CP += 1
   
   #def BINARY_OP( self, fn, type1, type2 ):
      # Weakly Typed Version
      #self.SS[-1] = (lambda x: self.SS[-1]   +   x)(self.SS.pop())
      #self.CP += 1
      
      # Strongly Typed Version
      #self.SS[-1] = (lambda x: type1(self.SS[-1])   +   type2(x))(self.SS.pop())
      #self.CP += 1
   
   def BINARY_OP2( self, fn, type1, type2 ):
      #'''Same as above but swapps the args to fn()'''
      arg2 = self.SS.pop( )
      #arg1 = self.SS[ -1 ]
      self.SS[ -1 ] = fn( type1(arg2), type2(self.SS[-1]) )
      self.CP += 1
   
   #def BINARY_OP2( self, fn, type1, type2 ):
      #self.SS[-1] = (lambda x: x   +   self.SS[-1])(self.SS.pop())
      #self.CP += 1
   
   def JUMP_OP( self ):
      self.CP = self.CS[ self.CP + 1 ]
   
   def CJUMP_OP( self, fn ):
      arg1 = self.SS.pop( )
      if fn(arg1):
         self.CP = self.CS[ self.CP + 1 ]
      else:
         self.CP += 2
   
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
      self.SS.append( self.CS[ self.CP + 1 ] )  # get operand
      self.CP += 2
   
   def op_POP( self ):                      # POP <count>
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
      operand = self.CS[ self.CP + 1 ]    # get operand
      result = self.SS[ 0 - operand : ]
      del self.SS[ 0 - operand : ]
      self.CP =+ 2

   def op_TOPSET( self ):                   # TOPSET <val>
      '''TOPSET <value>
      SS:  [ ..., <oldTop> ]  ->  [ ..., <value> ]
      :    Replace the stack's top item with <value>.
      #STACK
      '''
      operand = self.CS[ self.CP + 1 ]    # get operand
      self.SS[ -1 ] = val      
      self.CP += 2
   
   def op_PUSH_NTH( self ):
      '''PUSH_NTH <offset>
      SS:  [ ... ]  ->  [ ..., <nthItem>
      :    Push the nth (-1, -2, etc.) offset from the stack top.
      #STACK
      '''
      operand = self.CS[ self.CP + 1 ]    # get operand
      self.SS.append( self.SS[ 0 - operand ] )      
      self.CP += 2

   def op_SWAPXY( self ):
      '''SWAPXY
      SS:  [ ..., <x>, <y> ]  ->  [ ..., <y>, <x> ]
      :    Swap the two top stack items.
      #STACK
      '''
      self.SS[ 0 - 2 ], self.SS[ 0 - 1 ] = self.SS[ 0 - 2 : ]
      self.CP += 1

   # Environment Management
   def op_BIND( self ):
      '''BIND
      SS:  [ ..., <value>, <symbol> ]  ->  [ ..., <value> ]
      :    Bind a symbold to a value in the local namespace.
      #ENVIRONMENT
      '''
      name = self.SS.pop( )
      obj  = self.SS[ -1 ]
      self.ENV.declLocal( name, obj )
      self.CP += 1
   
   def op_BINDG( self ):
      '''BINDG
      SS:  [ ..., <value>, <symbol> ]  ->  [ ..., <value> ]
      :    Bind a symbol to a value in the global namespace.
      #ENVIRONMENT
      '''
      name = self.SS.pop( )
      obj  = self.SS[ -1 ]
      self.ENV.declGlobal( name, obj )
      self.CP += 1
   
   def op_UNBIND( self ):
      '''UNBIND
      SS:  [ ..., <symbol> ]  ->  [ ... ]
      :    Remove any bindings to the symbol.
      #ENVIRONMENT
      '''
      name = self.SS.pop( )
      self.ENV.unDecl( name )
      sefl.CP += 1

   def op_REBIND( self ):
      '''BIND
      SS:  [ ..., <value>, <symbol> ]  ->  [ ..., <value> ]
      :    Rebind a symbol to a new value.
      #ENVIRONMENT
      '''
      name = self.SS.pop( )
      obj  = self.SS[ -1 ]
      self.ENV.rebind( name, obj )
      self.CP += 1
   
   def op_DEREF( self ):
      '''DEREF
      SS:  [ ..., <symbol> ]  ->  [ ..., <value> ]
      :    Get value to which a symbol is bound.
      :    If <symbol> is not bound, <value> will be <symbol>
      #ENVIRONMENT
      '''
      name = self.SS[-1]
      self.SS[-1] = self.ENV.get( name )
      self.CP += 1
   
   def op_BEGIN( self ):
      '''BEGIN
      :    Begin/Open a new nested lexical scope in the environment.
      #ENVIRONMENT
      '''
      self.ENV = Environment( self.ENV )
      self.CP += 1
   
   def op_END( self ):
      '''END
      :    End/Close the current nested lexical scope in the environment.
      #ENVIRONMENT
      '''
      self.ENV = self.ENV.parentEnv( )
      self.CP += 1

   # Register Controls
   def op_PUSH_CS( self ):
      '''PUSH_CS
      SS:  [ ... ]  ->  [ ..., <saved CS> ]
      :    Push a copy of CS onto the stack.
      #REGISTERS
      '''
      self.SS.append( self.CS )
      self.CP += 1
   
   def op_POP_CS( self ):
      '''POP_CS
      SS:  [ ..., <saved CS> ]  ->  [ ... ]
      :    Pop the top of the stack, placing the popped value into CS.
      #REGISTERS
      '''
      self.CS = self.SS.pop( )
      self.CP += 1

   def op_PUSH_FLG( self ):
      '''PUSH_FLG
      SS:  [ ... ]  ->  [ ..., <saved FLG> ]
      :    Push a copy of FLG onto the stack.
      #REGISTERS
      '''
      self.SS.append( self.FLG )
      self.CP += 1

   def op_POP_FLG( self ):
      '''POP_FLG
      SS:  [ ..., <saved FLG> ]  ->  [ ... ]
      :    Pop the top of the stack, placing the popped value into FLG.
      #REGISTERS
      '''
      self.FLG = self.SS.pop( )
      self.CP += 1

   # Subroutine
   def op_CALL( self ):
      '''CALL <argumentCount>
      SS:  [ ..., <argn>, ..., <arg2>, <arg1>, <newCodeSeg> ]  -> [ ..., <argn>, ..., <arg2>, <arg1> ]
      :    Call the <newCodeSeg>.
      #CALL
      '''
      # Prepare new Stack Frame & Return Info
      newCodeSeg = self.SS.pop( )
      numArgs    = self.CS[self.CP+1]
      
      # Save current stack frame
      self.SP    = len(self.SS)     # SP set to stack top
      
      ret_SP = self.SP - numArgs
      ret_BP = self.BP
      ret_CS = self.CS
      ret_CP = self.CP + 2
      
      self.BINF  = [ret_CS, ret_CP, ret_SP, ret_BP, self.BINF]
      
      # Construct new stack frame
      self.BP    = self.SP             # BP points to argument 0
      self.CS    = newCodeSeg
      self.CP    = 0
   
   def op_CALLr( self ):
      '''CALLr <argumentCount>
      SS:  [ ..., <argn>, ..., <arg2>, <arg1> ]  -> [ ..., <argn>, ..., <arg2>, <arg1> ]
      :    Call the current Code Segment (CS) recursively.
      :    Optimization.  Equivalent to:  Push_CS; CALL <argumentCount>;
      #CALL OPTIMIZATION
      '''
      # Prepare new Stack Frame & Return Info
      newCodeSeg = self.CS
      numArgs    = self.CS[self.CP+1]
      
      # Save current stack frame
      self.SP    = len(self.SS)     # SP set to stack top
      
      ret_SP = self.SP - numArgs
      ret_BP = self.BP
      ret_CS = self.CS
      ret_CP = self.CP + 2
      
      self.BINF  = [ret_CS, ret_CP, ret_SP, ret_BP, self.BINF]
      
      # Construct new stack frame
      self.BP    = self.SP             # BP points to argument 0
      self.CS    = newCodeSeg
      self.CP    = 0
   
   def op_RET( self ):
      '''RET
      SS:  [ ..., <stack frame>, <return value> ]  ->  [ ..., <return value> ]
      :    Restore the prior stack frame being sure to preserve the return value.
      #CALL
      '''
      returnValue = self.SS.pop( )     # Save a copy of the return value
      self.CS, self.CP, self.SP, self.BP, self.BINF = self.BINF # Restore the caller's stack frame
      del self.SS[ self.SP : ]         # Pop all of the caller's arguments
      self.SS.append( returnValue )    # Restore the return value to the top of the stack
   
   def op_RETv( self ):
      '''RET <return value>
      SS:  [ ..., <old stack frame>, <current stack frame> ]  ->  [ ..., <old stack frame>, <return value> ]
      :    Restore the prior stack frame being sure to preserve the return value.
      :    Optimization.  Equivalent to: PUSH <return value>; RET;
      #CALL OPTIMIZATION
      '''
      returnValue = self.CS[ self.CP + 1 ]
      self.CS, self.CP, self.SP, self.BP, self.BINF = self.BINF # Restore the caller's stack frame
      del self.SS[ self.SP : ]         # Pop all of the caller's arguments
      self.SS.append( returnValue )    # Restore the return value to the top of the stack
   
   def op_PUSH_BPOFF( self ):
      '''PUSH_BPOFF <offest>
      SS:  [ ... ]  ->  [ ..., <value> ]
      :    Push the item at the indicated offset from the Base Pointer.
      :    e.g. -1 pushes the stack item at stack index [BP + <offset>],
      :    which is the first arguemnt to the current stack frame.
      #CALL
      '''
      offset = self.CS[ self.CP + 1 ]
      self.SS.append( self.SS[self.BP + offset] )
      self.CP += 2

   def op_CALLp( self ):
      '''CALLP
      SS:  [ ..., <python function> ]  ->  [ ... ]
      :    Call the python function.
      #CALLP
      '''
      pyFn       = self.SS.pop()
      numArgs    = self.CS[self.CP+1]
      
      oldCP      = self.CP
      try:
         pyFn( self, numArgs )
      except:
         self.FLG = self.UNKNOWN_UNRECOVERABLE
      if self.CP == oldCP:
         self.CP += 2

   # Basic Branching
   def op_HALT( self ):
      '''HALT
      : Terminate the current process.
      #BRANCH'''
      raise INTERRUPT( 'HALT' )
      #self.FLG = self.HALT
      #self.CP += 1

   def op_JMP( self ):
      '''JMP <address>
      :    Set the CP to <address>.
      #BRANCH
      '''
      self.JUMP_OP( )

   def op_JMP_T( self ):
      '''JMP_T <address>
      SS:  [ ..., <value> ]  ->  [ ... ]
      :    Set the CP to <address>, if <value> is true.
      #BRANCH
      '''
      self.CJUMP_OP( lambda x: x == True )

   def op_JMP_F( self ):
      '''JMP_F <address>
      SS:  [ ..., <value> ]  ->  [ ... ]
      :    Set the CP to <address>, if <value> is false.
      #BRANCH
      '''
      self.CJUMP_OP( lambda x: x == False )

   # Boolean Operations
   def op_bNOT( self ):
      '''bNOT
      SS:  [ ..., <value> ]  ->  [ ..., (boolean-not <value>) ]
      :    Unary-op; pop 1 arg, compute boolean-not from popped args, push result.
      #ALU.BOOLEAN
      '''
      self.BINARY_OP( op.not_, bool )

   def op_bAND( self ):
      '''bAND
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> boolean-AND <value2>) ]
      :    Binary-op; pop 2 args, compute boolean-and from popped args, push result.
      #ALU.BOOLEAN
      '''
      self.BINARY_OP( lambda x,y: x and y, bool, bool )

   def op_bOR( self ):
      '''bOR
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> boolean-OR <value2>) ]
      :    Binary-op; pop 2 args, compute boolean-or from popped args, push result.
      #ALU.BOOLEAN
      '''
      self.BINARY_OP( lambda x,y: x or y, bool, bool )

   # Bitwise Operations
   def op_iNEG( self ):
      '''iNEG
      SS:  [ ..., <value> ]  ->  [ ..., (bitwise-neg <value>) ]
      :    Unary-op; pop 1 arg, compute bitwise-negation from popped args, push result.
      #ALU.BITS
      '''
      self.BINARY_OP( op.invert, int )

   def op_iAND( self ):
      '''iAND
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> bitwise-AND <value2>) ]
      :    Binary-op; pop 2 args, compute bitwise-and from popped args, push result.
      #ALU.BITS
      '''
      self.BINARY_OP( op.and_, int, int )
   
   def op_iOR( self ):
      '''iOR
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> bitwise-OR <value2>) ]
      :    Binary-op; pop 2 args, compute bitwise-or from popped args, push result.
      #ALU.BITS
      '''
      self.BINARY_OP( op.or_, int, int )

   def op_iXOR( self ):
      '''iXOR
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> bitwise-XOR <value2>) ]
      :    Binary-op; pop 2 args, compute bitwise-xor from popped args, push result.
      #ALU.BITS
      '''
      self.BINARY_OP( op.xor, int, int )

   def op_iSHL( self ):
      '''iSHL
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> bitwise-XOR <value2>) ]
      :    Binary-op; pop 2 args, compute bitwise shift-left from popped args, push result.
      #ALU.BITS
      '''
      self.BINARY_OP( op.lshift, int, int )

   def op_iSHR( self ):
      '''iSHR
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> bitwise-XOR <value2>) ]
      :    Binary-op; pop 2 args, compute bitwise shift-right from popped args, push result.
      #ALU.BITS
      '''
      self.BINARY_OP( op.rshift, int, int )

   # Integer Oprations
   def op_iABS( self ):
      '''iABS
      SS:  [ ..., <value> ]  ->  [ ..., (absolute-value <value>) ]
      :    Unary-op; pop 1 arg, compute absolute value from popped args, push result.
      #ALU.INTEGER
      '''
      self.UNARY_OP( abs, int )

   def op_iCHSIGN( self ):
      '''iCHSIGN
      SS:  [ ..., <value> ]  ->  [ ..., (-1 * <value>) ]
      :    Unary-op; pop 1 arg, compute numerical negation from popped args, push result.
      #ALU.INTEGER
      '''
      self.UNARY_OP( op.neg, int )

   def op_iPROMOTE( self ): # int -> float
      '''iPROMOTE
      SS:  [ ..., <value> ]  ->  [ ..., (convert-to-float <value>) ]
      :    Unary-op; pop 1 arg, compute floating pointer equivalent, push result.
      #ALU.INTEGER
      '''
      self.UNARY_OP( float, int )

   def op_iEQ( self ):
      '''iEQ
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> == <value2>) ]
      :    Binary-op; pop 2 args; compute integer equality; push bolean result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.__eq__, int, int )
   
   def op_iNE( self ):
      '''iNE
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> != <value2>) ]
      :    Binary-op; pop 2 args; compute integer inequality; push bolean result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.__ne__, int, int )
   
   def op_iGT( self ):
      '''iGT
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> > <value2>) ]
      :    Binary-op; pop 2 args; compute integer inequality; push result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.__gt__, int, int )
   
   def op_iGE( self ):
      '''iGE
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> >= <value2>) ]
      :    Binary-op; pop 2 args; compute integer inequality; push bolean result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.__ge__, int, int )
   
   def op_iLT( self ):
      '''iLT
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> < <value2>) ]
      :    Binary-op; pop 2 args; compute integer inequality; push bolean result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.__lt__, int, int )
   
   def op_iLE( self ):
      '''iLE
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> <= <value2>) ]
      :    Binary-op; pop 2 args; compute integer inequality; push bolean result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.__le__, int, int )
   
   def op_iINC( self ):
      '''iINC
      SS:  [ ..., <value> ]  ->  [ ..., (<value> + 1) ]
      :    Unary-op; pop 1 arg; compute integer increment; push result.
      #ALU.INTEGER
      '''
      self.SS[-1] += 1
      self.CP += 1
   
   def op_iDEC( self ):
      '''iDEC
      SS:  [ ..., <value> ]  ->  [ ..., (<value> - 1) ]
      :    Unary-op; pop 1 arg; compute integer decrement; push result.
      #ALU.INTEGER
      '''
      self.SS[-1] -= 1
      self.CP += 1

   def op_iADD( self ):
      '''iADD
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> + <value2>) ]
      :    Binary-op; pop 2 args; compute integer sum; push result.
      #ALU.INTEGER
      '''
      SS = self.SS
      SS[-1] = int(SS.pop()) + int(SS[-1])
      self.CP += 1
   
   def op_iSUB( self ):
      '''iSUB
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> - <value2>) ]
      :    Binary-op; pop 2 args; compute integer difference; push result.
      #ALU.INTEGER
      '''
      SS = self.SS
      arg2 = SS.pop( )
      SS[-1] = SS[-1] - arg2
      #SS[-1] = int(SS[-1]) - int(arg2)
      #SS[-1] = (lambda x: int(SS[-1]) - x)(int(SS.pop()))
      self.CP += 1

   def op_iMUL( self ):   
      '''iMUL
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> * <value2>) ]
      :    Binary-op; pop 2 args; compute integer product; push result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.mul, int, int )

   def op_iDIV( self ):
      '''iMUL
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> / <value2>) ]
      :    Binary-op; pop 2 args; compute integer ratio; push result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.floordiv, int, int )
   
   def op_iMOD( self ):
      '''iMUL
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> modulo <value2>) ]
      :    Binary-op; pop 2 args; compute integer remainder; push result.
      #ALU.INTEGER
      '''
      self.BINARY_OP( op.mod, int, int )
   
   # IEEE Float Operations
   def op_fABS( self ):
      '''FABS
      SS:  [ ..., <value> ]  ->  [ ..., (absolute-value <value>) ]
      :    Unary-op; pop 1 arg, compute absolute value from popped args, push result.
      #ALU.FLOAT
      '''
      self.UNARY_OP( abs, float )

   def op_fCHSIGN( self ):
      '''ICHSIGN
      SS:  [ ..., <value> ]  ->  [ ..., (-1 * <value>) ]
      :    Unary-op; pop 1 arg, compute numerical negation from popped args, push result.
      #ALU.FLOAT
      '''
      self.UNARY_OP( op.neg, float )

   def op_fDEMOTE( self ):  # float -> int
      '''FDEMOTE
      SS:  [ ..., <value> ]  ->  [ ..., (convert-to-integer <value>) ]
      :    Unary-op; pop 1 arg, compute integer equivalent, push result.
      #ALU.FLOAT
      '''
      self.UNARY_OP( int, float )

   def op_fFRAC( self ):
      '''FFRAC
      SS:  [ ..., <value> ]  ->  [ ..., (fractionalPartOf <value>) ]
      :    Unary-op; pop 1 arg, compute fractional portion of, push result.
      #ALU.FLOAT
      '''
      self.UNARY_OP( lambda x:x - int(x), float )

   def op_fEQ( self ):
      '''FEQ
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> == <value2>) ]
      :    Binary-op; pop 2 args; compute equality; push bolean result.
      #ALU.FLOAT
      '''
      self.BINARY_OP( op.__eq__, float, float )
   
   def op_fNE( self ):
      '''FNE
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> != <value2>) ]
      :    Binary-op; pop 2 args; compute float inequality; push bolean result.
      #ALU.FLOAT
      '''
      self.BINARY_OP( op.__ne__, float, float )
   
   def op_fGT( self ):
      '''fGT
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> > <value2>) ]
      :    Binary-op; pop 2 args; compute float inequality; push result.
      #ALU.FLOAT
      '''
      self.BINARY_OP( op.__gt__, float, float )
   
   def op_fGE( self ):
      '''fGE
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> >= <value2>) ]
      :    Binary-op; pop 2 args; compute float inequality; push bolean result.
      #ALU.FLOAT
      '''
      self.BINARY_OP( op.__ge__, float, float )
   
   def op_fLT( self ):
      '''fLT
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> < <value2>) ]
      :    Binary-op; pop 2 args; compute float inequality; push bolean result.
      #ALU.FLOAT
      '''
      self.BINARY_OP( op.__lt__, float, float )
   
   def op_fLE( self ):
      '''fLE
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> <= <value2>) ]
      :    Binary-op; pop 2 args; compute float inequality; push bolean result.
      #ALU.FLOAT
      '''
      self.BINARY_OP( op.__le__, float, float )
   
   def op_fADD( self ):
      '''fADD
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> + <value2>) ]
      :    Binary-op; pop 2 args; compute float sum; push result.
      #ALU.FLOAT
      '''
      self.BINARY_OP( op.__add__, float, float )

   def op_fSUB( self ):
      '''fSUB
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> - <value2>) ]
      :    Binary-op; pop 2 args; compute float difference; push result.
      #ALU.FLOAT
      '''
      self.BINARY_OP( op.__sub__, float, float )
   
   def op_fMUL( self ):   
      '''fMUL
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> * <value2>) ]
      :    Binary-op; pop 2 args; compute float product; push result.
      #ALU.FLOAT
      '''
      self.BINARY_OP( op.__mul__, float, float )

   def op_fDIV( self ):
      '''fDIV
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> / <value2>) ]
      :    Binary-op; pop 2 args; compute float ratio; push result.
      #ALU.FLOAT
      '''
      self.BINARY_OP( op.__div__, float, float )
   
   def op_fPOW( self ):
      '''fPOW
      SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> ^ <value2>) ]
      :    Binary-op; pop 2 args; compute float power; push result.
      #ALU.FLOAT
      '''
      self.BINARY_OP( op.pow, float, float )

   def op_fLOG( self ):
      '''fLOG
      SS:  [ ..., <base>, <x> ]  ->  [ ..., (log <base> <x>) ]
      :    Binary-op; pop 2 args; compute float log; push result.
      #ALU.FLOAT
      '''
      self.BINARY_OP2( op.log, float, float )
   
   def op_fSIN( self ):
      '''fSIN
      SS:  [ ..., <theta> ]  ->  [ ..., (sine <theta>) ]
      :    Unary-op; pop 1 arg; compute sine; push result.
      #ALU.FLOAT
      '''
      self.UNARY_OP( math.sin, float )

   def op_fASIN( self ):
      '''fASIN
      SS:  [ ..., <theta> ]  ->  [ ..., (arcsine <theta>) ]
      :    Unary-op; pop 1 arg; compute arcsine; push result.
      #ALU.FLOAT
      '''
      self.UNARY_OP( math.asin, float )

   def op_fCOS( self ):
      '''fCOS
      SS:  [ ..., <theta> ]  ->  [ ..., (cosine <theta>) ]
      :    Unary-op; pop 1 arg; compute cosine; push result.
      #ALU.FLOAT
      '''
      self.UNARY_OP( math.cos, float )

   def op_fACOS( self ):
      '''fACOS
      SS:  [ ..., <theta> ]  ->  [ ..., (arccosine <theta>) ]
      :    Unary-op; pop 1 arg; compute arccosine; push result.
      #ALU.FLOAT
      '''
      self.UNARY_OP( math.acos, float )

   def op_fTAN( self ):
      '''fTAN
      SS:  [ ..., <theta> ]  ->  [ ..., (tangent <theta>) ]
      :    Unary-op; pop 1 arg; compute tangent; push result.
      #ALU.FLOAT
      '''
      self.UNARY_OP( math.tan, float )

   def op_fTAN2( self ):
      '''fATAN
      SS:  [ ..., <y>, <x> ]  ->  [ ..., (arctangent (<y>/<x>)) ]
      :    Binary-op; pop 2 args; compute arctangent; push result.
      #ALU.FLOAT
      '''
      self.BINARY_OP( math.atan2, float, float )

   def op_fATAN( self ):
      '''fATAN
      SS:  [ ..., <theta> ]  ->  [ ..., (arctangent <theta>) ]
      :    Unary-op; pop 1 arg; compute arctangent; push result.
      #ALU.FLOAT
      '''
      self.UNARY_OP( math.atan, float )

   # String Manipulation
   def op_sEQ( self ):
      pass
   
   def op_sNE( self ):
      pass
   
   def op_sGT( self ):
      pass
   
   def op_sGE( self ):
      pass
   
   def op_sLT( self ):
      pass
   
   def op_sLE( self ):
      pass
   
   def op_sLEN( self ):
      '''sLEN
      SS:  [ ..., <val:str> ]  ->  [ ..., (len <val:str>):int ]
      :    Unary-op; pop 1 arg; compute string length; push result.
      #ALU.STRING
      '''
      theString = self.SS[-1]
      self.SS[-1] = len(theString)
      self.CP += 1
   
   def op_sAT( self ):     # [ ..., string, index ]  =>  [ ..., character ]
      '''sAT
      SS:  [ ..., <val:str>, <index:int> ]  ->  [ ..., (<val>[ <index> ]):str ]
      :    Binary-op; pop 2 args; compute substring at index; push result.
      #ALU.STRING
      '''
      index = self.SS.pop()
      theString = self.SS[ -1 ]
      self.SS[ -1 ] = theString[index]
      self.CP += 1

   def op_sCAT( self ):
      '''sAT
      SS:  [ ..., <val2:str>, <val1:str> ]  ->  [ ..., (<val1> + <val2>):str ]
      :    Binary-op; pop 2 args; compute concatenation; push result.
      #ALU.STRING
      '''
      string2 = self.SS.pop()
      string1 = self.SS[-1]
      self.SS[-1] = string1 + string2
      self.CP += 1
   
   def op_sJOIN( self ):
      '''sAT
      SS:  [ ..., [<val1:str>, <val2:str>, ...], <sep:str> ]  ->  [ ..., (<val1> + <sep> + <val2> + <sep> + ...):str ]
      :    Binary-op; pop 2 args; compute join; push result.
      #ALU.STRING
      '''
      joinStr = self.SS.pop()
      strList = self.SS[-1]
      self.SS[-1] = joinStr.join( *strList )
      self.CP += 1

   def op_sSPLIT( self ):
      '''sSPLIT
      SS:  [ ..., <val:str>, <index:int> ]  ->  [ ..., <val>[:<index>], <val>[<index>:] ]
      :    Binary-op; pop 2 args; compute split; push substrings.
      #ALU.STRING
      '''
      index = self.SS.pop()
      theString = self.SS[-1]
      start = theString[ : index ]
      end   = theString[ index : ]
      self.SS[-1] = start
      self.SS.push(end)
      self.CP += 1
   
   def op_sTOINT( self ):  # [ ..., string ]  =>  [ ..., int(string) ]
      theString = self.SS[-1]
      self.SS[-1] = int(theString)
      self.CP += 1
   
   def op_sTOFLOAT( self ): # [ ..., string ]  =>  [ ..., float(string) ]
      theString = self.SS[-1]
      self.SS[-1] = float(theString)
      self.CP += 1
   
   # List Operations
   def op_lPACK( self ):       # [ obj1, obj2, ... objCount ]  =>  [ ..., [obj1, obj2, ...] ]
      count  = self.SS.pop( )
      values = self.SS[ 0 - count : ]
      del self.SS[ 0 - count - 1 : ]
      self.SS.append( values )
      self.CP += 1
   
   def op_lUNPACK( self ):     # [ list ] <- SP   =>   [ list-contents ] <- SP
      values = self.SS.pop( )
      count  = len(values)
      values.append( count )
      self.SS.extend( values )
      self.CP += 1
   
   def op_lREVERSE( self ):    # [ ..., list ]  =>  [ ..., reversed(list) ]
      theList = self.SS[-1].reverse()
      self.CP += 1

   def op_lLEN( self ):        # [ ..., list ]  =>  [ ..., len(list) ]
      theList = self.SS[ -1 ]
      self.SS[-1] = len(theList)
      self.CP += 1

   def op_lAT( self ):         # [ list, list-index ] <- SP  =>  [ list, list-item ]
      index = self.SS[ -1 ]
      aList = self.SS[ -2 ]
      self.SS[ -1 ] = aList[ index ]
      self.CP += 1
   
   def op_lATSET( self ):      # [ list, list-index, newValue ]  ;; modify list at list-index with newValue
      newValue = self.SS.pop( )
      index    = self.SS.pop( )
      theList  = self.SS[ -1 ]
      theList[ index ] = newValue
      self.CP += 1
   
   def op_lPUSH( self ):       # [ list, newItem ]
      newItem  = self.SS.pop( )
      theList  = self.SS[ -1 ]
      theList.push( newItem )
      self.CP += 1
   
   def op_lPOP( self ):        # [ list ]  =>  [ oldListTop ]
      theList  = self.SS[ -1 ]
      value    = theList.pop( )
      self.SS.append( value )
      self.CP += 1
   
   def op_lCAT( self ):        # [ list1, list2 ]  => [ <list-1-contents> <list-2-contents> ]
      list2 = self.SS.pop()
      list1 = self.SS[ -1 ]
      self.SS[ -1 ] = list1 + list2
      self.CP += 1
   
   def op_lSPLIT( self ):      # [ ..., aList, size ]  =>  [ ..., aList[ : size ], aList[ size : ] ]
      count = self.SS.pop( )
      theList = self.SS[ -1 ]
      self.SS[ -1 ] = theList[ : count ]
      self.SS.append( theList[ count : ] )
      self.CP += 1

   def op_lCOPY( self ):
      top = self.SS[ -1 ]
      top = copy.copy( top )
      self.SS.push( top )
      self.CP += 1
   
   def op_lSWAPSTACK( self ):  # [ ..., stack-A ] => [ ..., oldStack ]
      '''SWAPSTACK
      SS = currentStack           SS = alternateStack
      [..., alternateStack ]  =>  [ ..., currentStack ]
      '''
      newStack = self.SS.pop( )
      oldStack = self.SS
      self.SS = newStack
      newStack.push( oldStack )
      self.CP += 1
   
   def op_lPUSHNEWLIST( self ):      # push a new empty list onto the stack.
      self.SS.push( list() )
      self.CP += 1


import threading
import time
from queue import PriorityQueue

class Agent( threading.Thread ):
   requestID = 0
   
   def __init__( self, requestsQueue, resultsQueue, **kwds ):
      super().__init__( **kwds )
      self.setDaemon( 1 )
      self.workRequestQueue = PriorityQueue
      self.resultQueue      = PriorityQueue
      self.start( )
   
   def performWork( self, priority, callable, *args, **kwds ):
      Agent.requestID += 1
      self.workRequestQueue.put( (priority, (Agent.requestID, callable, args, kwds)) )
      return Agent.requestID

   def run( self ):
      while True:
         priority, request = self.workRequestQueue.get( )
         requestID, callable, args, kwds = request
         self.resultQueue.put( (requestID, callable(*args,**kwds)) )

def systemClockAgent( seconds=0.10 ):
   time.sleep( seconds )
   return 'clock-tick'
   

class InterruptableStackVM( StackVM1 ):
   def __init__( self ):
      super().__init__( )
 
   def run( self, CS ):
      self.reboot( CS )
      while True:
         self.handleIRQ( )
         self.IR = self.CS[ self.CP ]
         func = getattr( self, 'op_' + self.IR )
         func( )
         
         if self.FLG != 0:
            if self.FLG == self.HALT:
               break
   
   def handleIRQ( self ):
      irq,payload = self.IRQ.get( )
      
      func = getattr( self, 'irq_' + self.irq )
      func(payload)
  
   def reboot( self, CS, SS=None, ENV=None ):
      super().reboot( CS, SS, ENV )
      
      self.IRQ     = [ ]                       # Interrupts
      self.IV      = [ ]                       # Interrupt Handler Vector

   def op_IRQ_SEND( self ):
      '''Generate an interrupt request.'''
      pass
   
   def op_IRQ_SUSPEND( self ):
      '''Suspend interrupt handling.'''
      pass
   
   def op_IRQ_RESUME( self ):
      '''Resume interrupt handling.'''
      pass
   
   def irq_1( self, payload ):
      pass
   
   def irq_2( self, payload ):
      pass
   


def parseDoc( aDoc ):
   docIter     = iter(aDoc.splitlines())
   usage       = next(docIter)
   stackDoc    = ('','')
   descr       = ''
   cat         = ''
   try:
      op,sep,rest = docIter.partition(' ')
   except:
      op = usage
   
   for line in docIter:
      line = line.strip()
      if line.startswith( 'SS:' ):
         line = line[3:].strip()
         stackBefore, sep, stackAfter = line.partition( '->' )
         stackBefore = stackBefore.strip()
         stackAfter  = stackAfter.strip()
         stackDoc    = (stackBefore,stackAfter)
      elif line.startswith( ':' ):
         descr       = line[1:].strip()
      elif line.startswith( '#' ):
         cat         = line[1:].strip()
   return (op,usage,stackDoc,descr,cat)

def assemble( aProg ):
   # Two-Pass Assembler
   codeSeg     = [ ]
   localLabels = { }
   
   # Pass 1 - Catalog Labels
   address = 0
   for line in aProg:
      opcode   = line[0]
      operands = line[1:]
      if isinstance( opcode, str ) and (opcode[-1] == ':'):
         localLabels[opcode] = address
         
         opcode   = line[1]
         operands = line[2:]
      
      address += 1 + len(operands)

   # Pass 2 - Replace Jump Labels
   for address,line in enumerate(aProg):
      opcode   = line[0]
      operands = line[1:]
      if isinstance( opcode, str ) and (opcode[-1] == ':'):
         opcode   = line[1]
         operands = line[2:]
      
      codeSeg.append( opcode )
      
      for operand in operands:
         if isinstance( operand, str ) and (operand[-1] == ':'):
            operand = localLabels[operand]
         
         codeSeg.append( operand )

   return codeSeg

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
import collections

Instruction = collections.namedtuple( 'Instruction',
                                      [ 'label', 'opcode', 'operand1', 'operand2', 'operand3' ] )

Quad        = collections.namedtuple( 'Quad',
                                      [ 'opcode', 'operand1', 'operand2', 'operand3' ] )

Translator  = collections.namedtuple( 'Translator',
                                      [ 'fn','name','inputType','outputType' ] )

Translation = collections.namedtuple( 'Translation',
                                      [ 'payloadType','timestamp','payload'] )


class CodeObject1( object ):
   def __init__( self, opCodeMap, src=None, opt=None, obj=None, exe=None, labels=None, refs=None ):
      self.opCodeMap = opCodeMap
      self.set( src,opt,obj,exe,labels,refs )
   
   def set( self, src=None, nrm=None, opt=None, obj=None, exe=None, labels=None, refs=None ):
      if src is None:          # Source, Code as presented to the assembler.
         src = ''
      
      if nrm is None:          # Normalized Source, code parsed into 5-tuples (label,operand,opc1,opc2,opc3)
         nrm = [ ]
      
      if opt is None:          # Optimized Normalized Source,
         opt = [ ]
      
      if obj is None:          # Assembled Object Code
         obj = [ ]
      
      if exe is None:          # Linked Executable
         exe = [ ]
      
      if labels is None:       # Static symbol table
         labels = { }
      
      if refs is None:         # Static symbol reference lists
         refs = { }
      
      # Source Code Support
      self.sourceCode     = src
      self.normalizedCode = self._normalize( src )
      
      # Optimized Source Code Support
      self.optimizedCode  = opt
      
      # Assembled Object Code Support
      self.objectCode     = obj
      self.staticLabels   = labels
      self.staticRefs     = refs
      
      # Executable Code Support
      self.executableCode = exe
      
      self._xformStack    = [ ]
      self._codeStack     = [ ]
      self._toolSet       = { }
   
   def _normalize( self, source ): # src -> nrm
      # Clear generated objects.
      nrm                 = [ ]
      
      # Assembly Main Loop
      for line in source:
         label     = ''
         opcode    = ''
         operand1  = None
         operand2  = None
         operand3  = None
         
         idx = 0
         try:
            opcode  = line[idx]
            idx += 1
         except:
            continue
         
         if isinstance(opcode,str) and (opcode[-1] == ':'):
            label = opcode
            
            try:
               opcode = line[idx]
               idx += 1
            except:
               pass
        
         try:
            operand1 = line[idx]
            idx += 1
            operand2 = line[idx]
            idx += 1
            operand3 = line[idx]
         except:
            pass
       
         nrm.append( Instruction( label, opcode, operand1, operand2, operand3 ) )
      
      return nrm

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
      opt = PeepholeOptimizer()
      optimizedCode = opt.genOpt( self.normalizedCode )
   
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
         source = self.normalizedCode
   
      # Assembly Main Loop
      address = 0
      for instruction in source:
         if isinstance(instruction.label, str) and (len(instruction.label) > 0):
            staticLabels[instruction.label] = address
         
         if instruction.opcode:
            objectCode.append( instruction.opcode )
            address += 1
         
         operand = instruction.operand1
         if operand:
            objectCode.append( operand )
            if isinstance(operand,str) and (len(operand) > 0):
               staticRefs.setdefault(operand,[]).append(address)
            address += 1
         
         operand = instruction.operand2
         if operand:
            objectCode.append( operand )
            if isinstance(operand,str) and (lenoperand) > 0:
               staticRefs.setdefault(operand,[]).append(address)
            address += 1
         
         operand = instruction.operand3
         if operand:
            objectCode.append( operand )
            if isinstance(operand,str) and (lenoperand) > 0:
               staticRefs.setdefault(operand,[]).append(address)
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
            for refAddr in refList:
               exe[refAddr] = address
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
      
      for item in self.executableCode:
         #ptfn = CodeObject.frozenCall( self.opCodeMap, opcode, *operands )
         #newExe.append( ptfn )
         try:
            item_fn = self.opCodeMap[item]
         except:
            item_fn = item
         newExe.append( item_fn )
      
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


import datetime
class CodeObject( object ):
   TRANSLATORS = [
      Translator( )
      ]

   def __init__( self, src, formatName ):
      self.opCodeMap = opCodeMap
      self._original = Translation(formatName,datetime.datetime.now().isoformat(' '),src)
      self._results = [ self._original ]
   
   def rebuild( self ):
      self._results = [ self._original ]
      
      lastResult = self._original
      for xformFn,xformName,inputType,outputType in CodeObject2.TRANSLATORS:
         lastResult = xformFn( lastResult )
         completionTime = datetime.datetime.now().isoformat(' ')
         self._results.append( Translation(outputType,completionTime,lastResult) )
      
      self._results.reverse()
   

class TranslationPile( object ):
   def __init__( self, *xlaters ):
      self._pile = list(xlaters).reverse()
   
   def stack( ):
      return [ xformer.name for xformer in self._pile ].reverse( )
   
   def build( self, sourceObject, sourceType ):
      results = [ ]
      
      nextInput = None
      for name, fn, inputType, outputType in self._pile:
         if inputType == sourceType:
            nextInput = sourceObject
         
         if nextInput:
            output  = fn(nextInput)
            genTime = datetime.datetime.now().isoformat(' ')
            
            results.append( Translation(outputType,genTime,output) )
            nextInput = output
      
      results.reverse()
      return results

# target source 
translatorStack = [
   partialize
   ]
stackVM1_Asm_XLateStack = TranslationStack( )

class IntermediateCodeOptimizer( object ):
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

class IntermediateCodePeepholeOptimizer( object ):
   def __init__( self ):
      self._patterns = [
                       ######################################
                       ### Constant Folding Optimizations ###
                       
                       ###########################################
                       ### Strength Reduction - Speed Increase ###
                          # Match Pattern
                          [ [ Instruction('??L1', 'PUSH',    '$$A1', None, None ),
                              Instruction(None,   'RET',     None,   None, None ) ],
                            # >>> Output Pattern
                            [ Instruction('??L1', 'RETv',    '$$A1', None, None ) ] ],
                          
                          # Match Pattern
                          [ [ Instruction('??L1', 'PUSH_CS',  None,   None, None ),
                              Instruction(None,   'CALL',     '$$A1', None, None ) ],
                            # >>> Output Pattern
                            [ Instruction('??L1', 'CALLr',    '$$A1', None, None ) ] ],
                          
                          # Match Pattern
                          [ [ Instruction(None,   'JMP',      '$$L1', None, None ),
                              Instruction('$$L1', '??OP1',    '$$A1', None, None ) ],
                            # >>> Output Pattern
                            [ Instruction('??L1', '??OP1',    '$$A1', None, None ) ] ],
                       
                       ##################################################
                       ### Null Sequences - Delete Useless Operations ###      
                          
                       #####################################################
                       ### Combine Operations - Replace Several with One ###
                       
                       ############################################
                       ### Algebraic Laws - simplify or reorder ###
                       
                       ###########################################################################
                       ### Special Case Instructions - Use instructions used for special cases ###
                       ]
      
      self._optree = { }   # Map: OPCODE -> (Map:  OPCODE -> (Map:  OPCODE -> PATTERN))
      self._longestWindow = 0
      
      for sourcePattern, optimizedPattern in self._patterns:
         storagePath = [ instr.opcode for instr in sourcePattern ]
         self._storePattern( storagePath, (sourcePattern,optimizedPattern) )
         self._longestWindow = max( self._longestWindow, len(sourcePattern) )
      
      if self._longestWindow < 2:
         raise Exception( )
   
   def _storePattern( self, path, value ):
      key = '.'.join(path)
      self._optree[key] = value
   
   def _lookupPatterns( self, path ):
      key = '.'.join(path)
      return self._optree[key]

   def _deletePatterns( self, path ):
      key = '.'.join(path)
      del self._optree[key]
  
   def genOpt( self, sourceInstructions ):
      opt = [ ]
      
      srcIdx = 0
      while srcIdx < len(sourceInstructions):
         candidates = self.findPeepholeCandidates( sourceInstructions, srcIdx, self._longestWindow )
         if len(candidates) == 0:
            opt.append( sourceInstructions[srcIdx] )
            srcIdx += 1
         else:
            srcWindow = sourceInstructions[srcIdx:]
            for candidate in candidates:
               candidateSrcWindowPattern,candidateSrcWindowOpt = candidate
               result = self.tryGen( srcWindow, candidateSrcWindowPattern, candidateSrcWindowOpt )
               if result is not None:
                  if isinstance( result, list ):
                     opt.extend( result )
                     srcWindowLength = len(candidateSrcWindowPattern)
                     srcIdx += srcWindowLength
                     break
                  else:
                     raise Exception( )#  result should either be None or a list
            else:
               opt.append( sourceInstructions[srcIdx] )
               srcIdx += 1
      return opt

   def findPeepholeCandidates( self, sourceInstructions, idx, maxWindowSize ):
      '''Attempts to find a matching pattern among all stored patterns.
      sourceInstructions, a list of Instruction instances.
      idx,                indexed offset into sourceInstructions.
                          such that sourceInstructions[idx] represents the first
                          instruction in the source window.
      maxWndowSize,       The largest window size to try when when try to find
                          pattern matches.
      Returns a list of candidate pattern matches, worted with longest matchwindow first.
      '''
      candidates = [ ]
      windowSize = self._longestWindow
      try:
         while True:
            sourceWindow = sourceInstructions[ idx : idx + windowSize ]
            opcodeList   = [ instruction.opcode for instruction in sourceWindow ]
            try:
               candidates.append( self._lookupPatterns( opcodeList ) )
            except:
               pass
            if windowSize == 2:
               return candidates
            windowSize -= 1
      except:
         return candidates

   def tryGen( self, sourceWindow, patternWindow, outputPattern ):
      if len(sourceWindow) < len(patternWindow):
         return None
      
      # Create a map of string patterns in patternWindow to patterns in sourceWindow.
      # None,   in a pattern location means the corresponding source positions should contain None.
      #'$$var', If previously unseen, records a mapping of '$$var' to a corresponding non-None value.
      #         If previously encountered, verifies that '$$var' corresponds to the same mapping as it did previously.
      #'??var', If previously unseen, records a mapping of '??var' to a corresponding value; provided value is non-None otherwise nothing is recorded.
      #         If previously encountered, verifies that '$$var' corresponds to the same mapping as it did previously.
      carriedMapping = { }
      for sourceInstruction, patternInstruction in zip( sourceWindow, patternWindow ):
         updatedMapping = self._mappingAnalysis( sourceInstruction, patternInstruction, carriedMapping )
         if updatedMapping == False:
            return None
         carriedMapping = updatedMapping
      
      return self._mappingSynthesis( outputPattern, carriedMapping )
   
   def _mappingAnalysis( self, source, pattern, carriedMapping ):
      mapping = carriedMapping.copy()
      for srcLex,patLex in zip(source,pattern):
         if patLex is None:
            if (srcLex is not None) and (srcLex != ''):
               return False
         elif isinstance(patLex,str):
            if patLex.startswith('$$'):
               if patLex in mapping:
                  priorValue = mapping[patLex]
                  if srcLex != priorValue:
                     return False
               else:
                  if srcLex is None:
                     return False 
                  mapping[patLex] = srcLex
            elif patLex.startswith('??'):
               if patLex in mapping:
                  priorValue = mapping[patLex]
                  if srcLex != priorValue:
                     return False 
               else:
                  if (srcLex is not None) and (srcLex != ''):
                     mapping[patLex] = srcLex
            else:
               if srcLex != patLex:
                  return False
      
      return mapping

   def _mappingSynthesis( self, pattern, analysisMapping ):
      opt = [ ]
      for instruction in pattern:
         newInstruction = [ ]
         for patLex in instruction:
            if isinstance( patLex, str ):
               if patLex.startswith('$$'):
                  newInstruction.append( analysisMapping[patLex] )
               elif patLex.startswith('??'):
                  if patLex in analysisMapping:
                     newInstruction.append( analysisMapping[patLex] )
                  else:
                     newInstruction.append( None )
               else:
                  newInstruction.append( patLex )
            else:
               newInstruction.append( patLex )
         opt.append( Instruction(*newInstruction))
      return opt
   
   def insert_( self, tree, path, value ):
      key     = path.pop(0)
      if len(path) == 0:
         tree[key] = value
      else:
         subtree = tree.setdefault(key,         {})
         self._store( subtree, path[1:], value )

   def find_( self, tree, path, notFoundValue=None ):
      key = path.pop(0)
      if len(path) == 0:
         try:
            return tree[key]
         except:
            if notFoundValue:
               return notFoundValue
            raise
      else:
         try:
            subtree = tree[key]
            return self.find( subtree, path[1:], notFoundValue )
         except:
            if notFoundValue:
               return notFoundValue
            raise

   def delete_( self, tree, path ):
      key = path.pop(0)
      if len(path) == 0:
         del tree[key]
      else:
         self.delete( tree[key], path[1:] )


if __name__ == '__main__':
   vm = StackVM1( )
   fib = CodeObject1( vm.opcodes, src=[               # [ ..., arg ]
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH',                  2 ],
      [                  'iGT'                      ],
      [                  'JMP_T',           'else:' ],
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
   fib.optimize( )
   fib.assemble( )
   fib.link( )
   fib.partialize( )

   dbl = [
      [                  'PUSH_BPOFF',            0 ],
      [                  'PUSH',                  2 ],
      [                  'iMUL'                     ],
      [                  'RET'                      ]
   ]
   dbl_exe = assemble( dbl )
   
   _ = None
   sqr = [
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH_BPOFF',           -1 ],
      [                  'iMUL'                     ],
      [                  'RET'                      ]
   ]
   sqr_exe = assemble( sqr )
   
   def fact( n ):
      if n == 0:
         return 1
      else:
         return n * fact(n - 1)

   fct = [
      [                  'PUSH_BPOFF',            0 ],
      [                  'PUSH',                  0 ],
      [                  'iCMP'                     ],
      [                  'JMP_NE',          'else:' ],
      [                  'RETv',                  1 ],
      [ 'else:',         'PUSH_BPOFF',            0 ],
      [                  'PUSH_BPOFF',            0 ],
      [                  'iDEC'                     ],
      [                  'CALLr',                 1 ],
      [                  'iMUL'                     ],
      [ 'end:',          'RET'                      ]
   ]
   fct_exe = assemble( fct )
   
   prog = CodeObject1( vm.opcodes, src=[
      [                  'PUSH',                  20 ],
      [                  'PUSH',  fib.executableCode ],   # push the function
      [                  'CALL',                   1 ],   # call the function
      [                  'HALT'                      ]
   ] )
   prog.optimize( )
   prog.assemble( )
   prog.link( )
   prog.partialize( )
   
   from util_profile import PerfTimer
   
   entryPoint = prog.executableCode
   
   intructionCount = 0
   with PerfTimer( ):
      vm.run_p( entryPoint )   
      #instructionCount = vm.run_withTrace( entryPoint )

   print( vm.SS.pop() )
   PerfTimer.dump( )
   #if instructionCount > 0:
      #print( 'Number of vm instructions executed: {:d}.'.format(instructionCount))
   
   
   
   

class Environment( object ):
   SAVE          = [ ]

   def __init__( self, parent=None, primitives=None ):
      if primitives is None:
         primitives = { }
      
      self._parent     = parent
      self._locals     = { }
      self._primitives = primitives
      
      self.reInitialize( )

   def reInitialize( self ):
      root = self
      while root._parent is not None:
         root = root._parent
      
      root._locals = { name:value for name,value in self._primitives.items() }
      
      return root

   def parentEnv( self ):
      return self._parent

   def resetLocal( self ):
      self._locals        = { }

   def bind_g( self, aSymbol, aValue=None ):
      if isinstance( aSymbol, LSymbol):
         aSymbol = aSymbol._val
      
      self.GLOBAL_SCOPE[ aSymbol ] = aValue
      return aValue

   def bind( self, aSymbol, aValue=None ):
      if isinstance( aSymbol, LSymbol):
         aSymbol = aSymbol._val
      
      self._locals[ aSymbol ] = aValue
      return aValue

   def rebind( self, aSymbol, aValue ):
      return self._rebind( aSymbol, aValue, self )

   def get( self, aSymbol ):
      if aSymbol in self._locals:
         return self._locals[ aSymbol ]
      elif self._parent is None:
         return None
      else:
         return self._parent.get( aSymbol )

   def _rebind( self, aSymbol, aValue, localScope ):
      if aSymbol in self._locals:
         self._locals[ aSymbol ] = aValue
         return aValue
      elif self._parent is None:
         return localScope.declLocal( aSymbol, aValue )
      else:
         return self._parent._rebind( aSymbol, aValue, localScope )
   
   def set_nonRecursive( self, sym, value ):
      if isinstance( sym, LSymbol ):
         symStr = sym._val
      else:
         symStr = sym
      
      scope = self
      while scope is not None:
         if symStr in scope._locals:
            scope._locals[ symStr ] = value
            return value
         else:
            scope = scope._parent
      
      self._locals[ symStr ] = value
      return value
 
   def get_nonRecursive( self, sym ):
      if isinstance( sym, LSymbol ):
         symStr = sym._val
      else:
         symStr = sym
      
      scope = self
      while scope is not None:
         try:
            return scope._locals[ symStr ]
         except:
            scope = scope._parent
      
      return sym

   def unbind( self, aSymbol ):
      if aSymbol in self._locals:
         del self._locals[aSymbol]
      elif self._parent is None:
         return
      else:
         self._parent.unset(aSymbol)

   def unbind_nonRecursive( self, sym ):
      if isinstance( sym, LSymbol ):
         symStr = sym._val
      else:
         symStr = sym
      
      scope = self
      while scope is not None:
         if symStr in scope._locals:
            del scope._locals[ symStr ]
         else:
            scope = scope._parent
      
      return sym

   def isBound( self, aSymbol ):
      if aSymbol in self._locals:
         return True
      elif self._parent is None:
         return False
      else:
         return self._parent.isBound( aSymbol )

   def localSymbols( self ):
      return sorted( self._locals.keys() )
   
   def parentEnv( self ):
      return self._parent

   def saveSymTab( self ):
      PkEnvironment.SAVE.append( self._locals.copy() )

   def restoreSymTab( self ):
      self._locals = PkEnvironment.SAVE.pop( )

   def _global( self ):
      scope = self
      while scope._parent is not None:
         scope = scope._parent
      
      return scope

   def __iter__( self ):
      if self._parent is None:
         return iter( self._locals )
      else:
         return itertools.chain( self._locals, self._parent )



'''
BIND      [ ..., value, name, namespace/env ] <== top
Binds the value to the name in the provided namespace/env.

UNBIND    [ ..., name, namespace/env ] <== top
Removes the binding of name to 

DEREF     [ ..., name, namespace/env ] <== top
Returns the value bound to name in the provided namespace/env.

DECALL    [ ..., arguments, name, namespace/env ] <== top
Calls the name in the namepaces provided.

ISBOUND   [ ..., name, namespace/env ] <== top
Is the name bound in the namespace?

PUSHNEWNS [ ... ] <== top

push <namespace>
push 'parent'
pushnewns
bind
'''

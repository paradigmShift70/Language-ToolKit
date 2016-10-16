import tkinter
import tkinter.font
import ltk_py3.Listener as Listener
import Puck

Card = Listener.Card

class ActiveListbox( tkinter.Listbox ):
   def __init__( self, *args, **kwds ):
      selectcommand = kwds.pop( 'selectcommand', None )
      super().__init__( *args, **kwds )
      self._selectCommand = selectcommand
      self._currentSelection = None
   
   def startPolling( self ):
      self._poll( )
   
   def _poll( self ):
      now = self.curselection()
      if now != self._currentSelection:
         try:
            self._selectCommand( )
         except:
            pass
         self._currentSelection = now

      if len(self._currentSelection) > 0:
         self.selection_set( self._currentSelection[0] )
      
      self.after( 250, self._poll )


class CardStack( object ):
   def __init__( self ):
      self._impl = [ ]
   
   def newEntry( self, value, selectNewCard=True ):
      self._current = len(self._impl)
      self._impl.append( value )
   
   def delEntry( self, index ):
      try:
         del self._impl[ index ]
      except:
         pass

   def __getitem__( self, index ):
      return self._impl[ index ]

   def __setitem__( self, index, value ):
      self._impl[ index ] = value

   def cardList( self ):
      return list( range(len(self._impl)) )
   
   def moveUp( self, index ):
      if (index >= 1) and (index < len(self._impl)):
         item = self._impl.pop(index)
         self._impl.insert( index - 1, item )
         return True
      else:
         return False
   
   def moveDown( self, index ):
      if (index >= 0) and (index < (len(self._impl) - 2)):
         item = self._impl.pop(index)
         self._impl.insert( index + 1, item )
         return True
      elif index == (len(self._impl) - 2):
         item = self._impl.pop(index)
         self._impl.append( item )
         return True
      else:
         return False

class CursorCardStack( CardStack ):
   def __init__( self ):
      super().__init__( )
      self._curIdx = None

   def getCursorIndex( self ):
      return self._curIdx

   def setCursorIndex( self, index ):
      if (index >= 0) and (index < len(self._impl)):
         self._curIdx = index

   def newEntry( self, value, moveCursor=True ):
      newCardIdx = len(self._impl)
      try:
         self._impl.append( value )
      except:
         raise
   
      if moveCursor:
         self._curIdx = newCardIdx
      
      return newCardIdx
   
   def getCurrent( self ):
      return self._impl[ self._curIdx ]

   def commitCurrent( self, newValue ):
      if self._curIdx is not None:
         self._impl[ self._curIdx ] = newValue

   def delCurrent( self ):
      self.delEntry( self._curIdx )
      
      if self._curIdx >= len(self._impl):
         self._curIdx = len(self._impl) - 1
      elif self._curIdx < 0:
         self._curIdx = 0
   
   def moveUp_current( self ):
      if self.moveUp( self._curIdx ):
         self._curIdx -= 1
   
   def moveDown_current( self ):
      if self.moveDown( self._curIdx ):
         self._curIdx += 1


class ListenerWindow( tkinter.Frame ):
   def __init__( self, master, listener, *args, **kwds ):
      super().__init__( master, *args, **kwds )
   
      self._listener = listener
      self._cards    = CursorCardStack( )
      self._current  = Card('','','','','',0)
      
      self._costVar  = tkinter.StringVar( self )
      
      font = 'Consolas 12'
      gutterwidth = 4
      gutterbg    = 'gray'
      gutterfg    = 'yellow'
      textwidth   = 80
      textheight  = 20
      textbg      = 'black'
      textfg      = 'orange'
      
      self._ctrlFrm = tkinter.Frame( self )
      self._ctrlFrm.pack( side=tkinter.LEFT, anchor='n', fill=tkinter.Y )
      
      self._cardFrm = tkinter.Frame( self._ctrlFrm, borderwidth=3, relief=tkinter.SUNKEN )
      self._cardFrm.pack( side=tkinter.TOP, anchor='w', fill=tkinter.Y, ipadx=3, ipady=3, padx=3, pady=3 )
      
      self._cardLst = ActiveListbox( self._cardFrm, font=font, width=4, selectcommand=self._selectCard )
      self._cardLst.pack( side=tkinter.LEFT, anchor='n', fill=tkinter.Y )
      
      self._cardLSb = tkinter.Scrollbar( self._cardFrm, orient=tkinter.VERTICAL, borderwidth=2, elementborderwidth=3 )
      self._cardLSb.pack( side=tkinter.LEFT, anchor='n', fill=tkinter.Y )
      
      self._cardLbCtrlFrm = tkinter.Frame( self._cardFrm )
      self._cardLbCtrlFrm.pack( side=tkinter.LEFT, anchor='n', fill=tkinter.Y, padx=5 )
      
      self._cardLbNew = tkinter.Button( self._cardLbCtrlFrm, font=font, text='New', command=self._newCard )
      self._cardLbNew.pack( side=tkinter.TOP, fill=tkinter.X )
      
      self._cardLbMoveUp = tkinter.Button( self._cardLbCtrlFrm, font=font, text='Move Up', command=self._moveUp )
      self._cardLbMoveUp.pack( side=tkinter.TOP, fill=tkinter.X )
      
      self._cardLbMoveDn = tkinter.Button( self._cardLbCtrlFrm, font=font, text='Move Down', command=self._moveDn )
      self._cardLbMoveDn.pack( side=tkinter.TOP, fill=tkinter.X )
      
      self._cardLbDelete = tkinter.Button( self._cardLbCtrlFrm, font=font, text='Delete', command=self._delete )
      self._cardLbDelete.pack( side=tkinter.TOP, fill=tkinter.X )
      
      self._evalBtn = tkinter.Button( self._ctrlFrm, font=font, text='Eval', command=self._evalTxt )
      self._evalBtn.pack( side=tkinter.TOP,  anchor='w', fill=tkinter.NONE )
      
      self._costFrm = tkinter.Frame( self._ctrlFrm, relief=tkinter.GROOVE, borderwidth=3 )
      self._costFrm.pack( side=tkinter.TOP, anchor='w', fill=tkinter.NONE )
      
      self._costLbl = tkinter.Label( self._costFrm, font=font, text='Time:')
      self._costLbl.pack( side=tkinter.LEFT, anchor='n', fill=tkinter.NONE )
      self._costVal = tkinter.Label( self._costFrm, font=font, textvariable=self._costVar )
      self._costVal.pack( side=tkinter.LEFT, anchor='n', fill=tkinter.NONE )
      
      self._gutter  = tkinter.Text( self, background=gutterbg, foreground=gutterfg, font=font, width=gutterwidth, height=textheight )
      self._gutter.pack( side=tkinter.LEFT, anchor='n', fill=tkinter.Y )
      
      self._text = tkinter.Text( self, background=textbg, foreground=textfg, font=font, width=textwidth, height=textheight, insertwidth=7, insertborderwidth=2, insertbackground='yellow', insertontime=500 )
      self._text.pack( side=tkinter.LEFT, anchor='n', fill=tkinter.Y )
      
      self._sb   = tkinter.Scrollbar( self, orient=tkinter.VERTICAL, borderwidth=2, elementborderwidth=3 )
      self._sb.pack( side=tkinter.LEFT, anchor='n', fill=tkinter.Y )
      
      self._gutter[ 'yscrollcommand' ] = self._sb.set
      self._text[   'yscrollcommand' ] = self._sb.set
      
      self._sb[ 'command' ] = self._scroll
      
      self._gutter.insert( tkinter.END, self.genGutterText(40,gutterwidth) )
      self._gutter[ 'state' ] = tkinter.DISABLED
      
      self._newCard( )
      self._updateCardStack( )
      self._cardLst.startPolling( )

   def genGutterText( self, ct=50, gutterWidth=5 ):
      gutterLineLst = [ str(x) for x in range( 1, ct+1 ) ]
      formattedGutterLineLst = [ x.rjust(gutterWidth) for x in gutterLineLst ]
      return '\n'.join(formattedGutterLineLst)

   def _scroll( self, *args ):
      if (args[0] == 'moveto'):
         self._gutter.yview_moveto( args[1])
         self._text.yview_moveto( args[1])
      
      else:
         self._gutter.yview_scroll( args[1])
         self._text.yview_scroll( args[1])
      
      return 'break'

   def _evalTxt( self, evt=None ):
      inputText = self._text.get( '1.0', tkinter.END )
      
      response = self._listener.instrumentedEval( inputText )
      inputText, retVal, console, pr_err, ev_err, cost = response
      
      self._costVar.set( '{:10.5f} sec'.format(cost) )
      
      lines = [ '... ' + ln for ln in inputText.splitlines() ]
      lines[0] = lines[0].replace( '... ', '>>> ')
      
      print( '\n'.join(lines) )
      print( '... ')
      print( console )
      print( '==> ')
      print( retVal )
      print( '======================== (Completed in {:16.5f} sec)'.format(cost))
      self._current = response
   
   def _updateCardStack( self ):
      valLst = self._cards.cardList( )
      curIdx = self._cards.getCursorIndex( )
      
      self._cardLst.delete( 0, tkinter.END )
      self._cardLst.insert( 0, *valLst )
      
      self._cardLst.selection_set( curIdx )
      self._cardLst.see( curIdx )

   def _newCard( self ):
      newCardIndex = self._cards.newEntry( Card('','','','','',0), moveCursor=False )
      self._selectCard( newCardIndex )

   def _moveUp( self ):
      self._cards.moveUp_current( )
      self._updateCardStack( )
   
   def _moveDn( self ):
      self._cards.moveDown_current( )
      self._updateCardStack( )
   
   def _delete( self ):
      self._text.delete( '1.0', tkinter.END )
      self._cards.delCurrent( )
      selIdx = self._cards.getCursorIndex( )
      self._updateCardStack( )
      self._selectCard( selIdx, nocommit=True )

   def _selectCard( self, index=None, nocommit=False ):
      if nocommit == False:
         self._commitCurrentCard( )
      
      if index is None:
         selIdx = self._cardLst.curselection()[0]
      else:
         selIdx = index
      
      self._cards.setCursorIndex( selIdx )
      
      self._current = self._cards.getCurrent()
      
      self._updateCardStack( )
      self._text.delete( '1.0', tkinter.END )
      self._text.insert( tkinter.END, self._current.expression )
   
   def _commitCurrentCard( self ):
      expression,response,pr_err,ev_err,console,cost = self._current
      
         # !!! UGLY CODE WARNING !!!
      expression = self._text.get( '1.0', tkinter.END )[ : -1 ]
         # Text.get() appends a '\n'. Remove it here:  ^^^^^^^^
      
      self._current = Card(expression,response,pr_err,ev_err,console,cost)
      self._cards.commitCurrent( self._current )

if __name__=='__main__':
   interp = Puck.PuckInterpreter()
   listener = Listener.Listener( interp, language='Puck', version='0.1' )
   
   root = tkinter.Tk()
   win = ListenerWindow( root, listener )
   win.pack()
   
   #print(sorted(tkinter.font.families(root)))
   
   root.mainloop()
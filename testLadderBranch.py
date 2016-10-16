import time


def select__8( var ):
   '''select on var [0 .. 7] (3 search max).'''
   if var < 4:
      if var < 2:
         if var == 0:                            #   0
            pass
         else:                                   #   1
            pass
      elif var == 2:                             #   2
         pass
      else:                                      #   3
         pass
   elif var < 6:
      if var == 4:                               #   4
         pass
      else:                                      #   5
         pass
   elif var == 6:                                #   6
      pass
   else:                                         #   7
      pass


def select_16( var ):
   '''select on var [0 .. 15] (4 search max).'''
   if var < 8:
      if var < 4:
         if var < 2:
            if var == 0:                         #   0
               pass
            else:                                #   1
               pass
         elif var == 2:                          #   2
            pass
         else:                                   #   3
            pass
      elif var < 6:
         if var == 4:                            #   4
            pass
         else:                                   #   5
            pass
      elif var == 6:                             #   6
         pass
      else:                                      #   7
         pass
   elif var < 12:
      if var < 10:
         if var == 8:                            #   8
            pass
         else:                                   #   9
            pass
      elif var == 10:                            #  10
         pass
      else:                                      #  11
         pass
   elif var < 14:
      if var == 12:                              #  12
         pass
      else:                                      #  13
         pass
   elif var == 14:                               #  14
      pass
   else:                                         #  15
      pass


def select_32( var ):
   '''select on var [0 ..  32] (5 search max).'''
   if var < 16:
      if var < 8:
         if var < 4:
            if var < 2:
               if var == 0:                      #   0
                  pass
               else:                             #   1
                  pass
            elif var == 2:                       #   2
               pass
            else:                                #   3
               pass
         elif var < 6:
            if var == 4:                         #   4
               pass
            else:                                #   5
               pass
         elif var == 6:                          #   6
            pass
         else:                                   #   7
            pass
      elif var < 12:
         if var < 10:
            if var == 8:                         #   8
               pass
            else:                                #   9
               pass
         elif var == 10:                         #  10
            pass
         else:                                   #  11
            pass
      elif var < 14:
         if var == 12:                           #  12
            pass
         else:                                   #  13
            pass
      elif var == 14:                            #  14
         pass
      else:                                      #  15
         pass
   elif var < 24:
      if var < 20:
         if var < 18:
            if var == 16:                        #  16
               pass
            else:                                #  17
               pass
         elif var == 18:                         #  18
            pass
         else:                                   #  19
            pass
      elif var < 22:
         if var == 20:                           #  20
            pass
         else:                                   #  21
            pass
      elif var == 22:                            #  22
         pass
      else:                                      #  23
         pass
   elif var < 28:
      if var < 26:
         if var == 24:                           #  24
            pass
         else:                                   #  25
            pass
      elif var == 26:                            #  26
         pass
      else:                                      #  27
         pass
   elif var < 30:
      if var == 38:                              #  28
         pass
      else:                                      #  29
         pass
   elif var == 30:                               #  30
      pass
   else:                                         #  31
      pass



def select_64( var, f ):
   '''select on var [0 ..  64] (6 search max).'''
   '''select on var [0 .. 128] (7 search max).'''
   '''select on var [0 .. 257] (8 search max).'''
   if var < 32:
      if var < 16:
         if var < 8:
            if var < 4:
               if var < 2:
                  if var == 0:                      #   0
                     pass
                  else:                             #   1
                     pass
               elif var == 2:                       #   2
                  pass
               else:                                #   3
                  pass
            elif var < 6:
               if var == 4:                         #   4
                  pass
               else:                                #   5
                  pass
            elif var == 6:                          #   6
               pass
            else:                                   #   7
               pass
         elif var < 12:
            if var < 10:
               if var == 8:                         #   8
                  pass
               else:                                #   9
                  pass
            elif var == 10:                         #  10
               pass
            else:                                   #  11
               pass
         elif var < 14:
            if var == 12:                           #  12
               pass
            else:                                   #  13
               pass
         elif var == 14:                            #  14
            pass
         else:                                      #  15
            pass
      elif var < 24:
         if var < 20:
            if var < 18:
               if var == 16:                        #  16
                  pass
               else:                                #  17
                  pass
            elif var == 18:                         #  18
               pass
            else:                                   #  19
               pass
         elif var < 22:
            if var == 20:                           #  20
               pass
            else:                                   #  21
               pass
         elif var == 22:                            #  22
            pass
         else:                                      #  23
            pass
      elif var < 28:
         if var < 26:
            if var == 24:                           #  24
               pass
            else:                                   #  25
               pass
         elif var == 26:                            #  26
            pass
         else:                                      #  27
            pass
      elif var < 30:
         if var == 38:                              #  28
            pass
         else:                                      #  29
            pass
      elif var == 30:                               #  30
         pass
      else:                                         #  31
         pass

   if var < 16:
      if var < 8:
         if var < 4:
            if var < 2:
               if var == 0:                      #   0
                  pass
               else:                             #   1
                  pass
            elif var == 2:                       #   2
               pass
            else:                                #   3
               pass
         elif var < 6:
            if var == 4:                         #   4
               pass
            else:                                #   5
               pass
         elif var == 6:                          #   6
            pass
         else:                                   #   7
            pass
      elif var < 12:
         if var < 10:
            if var == 8:                         #   8
               pass
            else:                                #   9
               pass
         elif var == 10:                         #  10
            pass
         else:                                   #  11
            pass
      elif var < 14:
         if var == 12:                           #  12
            pass
         else:                                   #  13
            pass
      elif var == 14:                            #  14
         pass
      else:                                      #  15
         pass
   elif var < 24:
      if var < 20:
         if var < 18:
            if var == 16:                        #  16
               pass
            else:                                #  17
               pass
         elif var == 18:                         #  18
            pass
         else:                                   #  19
            pass
      elif var < 22:
         if var == 20:                           #  20
            pass
         else:                                   #  21
            pass
      elif var == 22:                            #  22
         pass
      else:                                      #  23
         pass
   elif var < 28:
      if var < 26:
         if var == 24:                           #  24
            pass
         else:                                   #  25
            pass
      elif var == 26:                            #  26
         pass
      else:                                      #  27
         pass
   elif var < 30:
      if var == 38:                              #  28
         pass
      else:                                      #  29
         pass
   elif var == 30:                               #  30
      pass
   else:                                         #  31
      pass




class VM( object ):
   def __init__( self ):
      self.x = 0

      self.op = {
         0 : self.do_X,
         1 : self.do_X,
         2 : self.do_X,
         3 : self.do_X,
         4 : self.do_X,
         5 : self.do_X,
         6 : self.do_X
         }

   def call( self, op, f ):
      return self.op[op]( f )

   def do_X( self, f ):
      return f( )


if __name__ == '__main__':
   iterations = 100000
   print( 'Testing Seive / process_time ({:d} iterations)'.format(iterations) )
   tot = 0
   for x in range( iterations ):
      delta  = select_32( 0, time.process_time )
      tot   += delta
   print( '    avg. {:12.5f}'.format(tot) )
   print( )

   print( 'Testing Seive / perf_counter ({:d} iterations)'.format(iterations) )
   tot = 0
   for x in range( iterations ):
      delta  = select_32( 0, time.perf_counter )
      tot   += delta
   print( '    avg. {:12.5f}'.format(tot) )
   print( )

   vm = VM()

   print( 'Testing DictCall / process_time ({:d} iterations)'.format(iterations) )
   tot = 0
   for x in range( iterations ):
      start = time.process_time()
      vm.call( 0, time.process_time )
      end   = time.process_time()
      tot   += end - start
   print( '    avg. {:12.5f}'.format(tot) )
   print( )

   print( 'Testing DictCall / perf_counter ({:d} iterations)'.format(iterations) )
   tot = 0
   for x in range( iterations ):
      start = time.perf_counter()
      vm.call( 0, time.perf_counter )
      end   = time.process_time()
      tot   += end - start
   print( '    avg. {:12.5f}'.format(tot) )
   print( )


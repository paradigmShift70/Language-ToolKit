from ltk_py3.stackvm import *

'''
fib( arg ):
   if arg <= 2:
      return 1
   else:
      return fib(arg-1) + fib(arg-2)

Sequence:  1   1   2   3   5   8  13  21  34  55
Position:  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15
'''

if __name__ == '__main__':
   fib = [               # [ ..., arg ]
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH',                  2 ],
      [                  'iCMP'                     ],
      [                  'JMP_GT',          'else:' ],
      [                  'PUSH',                  1 ],
      [                  'JMP',             'end:'  ],
      [ 'else:',         'PUSH_BPOFF',           -1 ],
      [                  'iDEC'                     ],
      [                  'RECURSE2',              1 ],   # Recursive call
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH',                  2 ],
      [                  'iSUB'                     ],
      [                  'RECURSE2',              1 ],   # Recursive call
      [                  'iADD'                     ],
      [ 'end:',          'RET2'                     ]
   ]
   fib_exe = assemble( fib )

   _ = None
   square = [
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH_BPOFF',           -1 ],
      [                  'iMUL'                     ],
      [                  'RET'                      ]
   ]
   square_exe = assemble( square )
   
   prog = [
      [                  'PUSH',                 10 ],
      [                  'PUSH',              'num' ],
      [                  'DEF'                      ],
      [                  'POP'                      ],
      [                  'PUSH',                 10 ],
      [                  'PUSH',                  6 ],
      [                  'iSUB'                     ],
      [                  'POP'                      ],
      [                  'PUSH',              'num' ],
      [                  'GET'                      ],
      [                  'CALL',         fib_exe, 1 ],
      [                  'HALT'                     ]
   ]
   prog_exe = assemble( prog )   
   #executable  = static_link( binary, symTab )   
   
   prog2 = [
      [                  'PUSH',                 10 ],
      [                  'CALL2',        fib_exe, 1 ],
      [                  'HALT'                     ]
   ]
   prog2_exe = assemble( prog2 )
   
   vm = StackVM( )
   
   from perftesting import PerfTimer
   
   with PerfTimer( ):
      vm.run( prog2_exe )   
      #vm.run_withTrace( prog2_exe )   

   print( vm.SS.pop() )
   PerfTimer.dump( )
   
   
   
   
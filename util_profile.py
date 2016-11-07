
from time import perf_counter,process_time
import contextlib


timer = process_time

class PerfTimer( object ):
   STATS = [ ]
   
   def __init__( self, doc='### testing ###' ):
      self._doc           = doc
      self._startTime     = 0
      self.totalTime      = 0

   def __enter__( self ):
      self.totalTime      = 0
      self._startTime     = timer( )
      return self
   
   def __exit__( self, *exc ):
      endTime = timer()
      self.totalTime = endTime - self._startTime
      
      PerfTimer.STATS.append( (self._doc, self.totalTime) )
   
   @staticmethod
   def dump( ):
      for title,perf in PerfTimer.STATS:
         print( title )
         print( '   --- Performance test time:  {0:12.5f} Sec'.format(perf) )
         print( )

if __name__ == '__main__':
   numIterations = 1000
   
   testName = 'List element access: [0].'
   lst = [ 10*x for x in range(5000) ]
   with PerfTimer( testName ):
      for x in range(numIterations):
         y = lst[0]
   
   testName = 'List element access: [5000].'
   lst = [ 10*x for x in range(5000) ]
   with PerfTimer( testName ):
      for x in range(numIterations):
         y = lst[4999]
   
   PerfTimer.dump( )
   
   
   
   
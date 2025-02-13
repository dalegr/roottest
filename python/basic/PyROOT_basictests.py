# File: roottest/python/basic/PyROOT_basictests.py
# Author: Wim Lavrijsen (LBNL, WLavrijsen@lbl.gov)
# Created: 11/23/04
# Last: 06/09/15

"""Basic unit tests for PyROOT package."""

import sys, os, unittest
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import ROOT
from ROOT import gROOT, gApplication, gSystem, gInterpreter, gDirectory
from ROOT import TLorentzVector, TCanvas, TString, TList, TH1D, TObjArray, TVectorF, TObjString
from common import *

__all__ = [
   'Basic1ModuleTestCase',
   'Basic2SetupTestCase',
   'Basic3PythonLanguageTestCase',
   'Basic4ArgumentPassingTestCase',
   'Basic5PythonizationTestCase',
   'Basic6ReturnValueTestCase',
]

def setup_module(mod):
    if not os.path.exists('SimpleClass.C'):
        os.chdir(os.path.dirname(__file__))

### basic module test cases ==================================================
class Basic1ModuleTestCase( MyTestCase ):
   def test1Import( self ):
      """Test import error handling"""

      def failImport():
         from ROOT import GatenKaas

      self.assertRaises( ImportError, failImport )


### basic functioning test cases =============================================
class Basic2SetupTestCase( MyTestCase ):
   def test1Globals( self ):
      """Test the availability of ROOT globals"""

      self.assert_( gROOT )
      self.assert_( gApplication )
      self.assert_( gSystem )
      self.assert_( gInterpreter )
      self.assert_( gDirectory )

   def test2AccessToGlobals( self ):
      """Test overwritability of ROOT globals"""

      import ROOT
      oldval = ROOT.gDebug

      ROOT.gDebug = -1
      self.assert_(gROOT.ProcessLine('gDebug == -1'))

      ROOT.gDebug = oldval

   def test3AccessToGlobalsFromROOT( self ):
      """Test creation and access of new ROOT globals"""

      import ROOT
      ROOT.gMyOwnGlobal = 3.1415

      proxy = gROOT.GetGlobal( 'gMyOwnGlobal', 1 )
      try:
         self.assertEqual( proxy.__get__( proxy ), 3.1415 )
      except AttributeError:
         # In the old PyROOT, if we try to bind a new global,
         # such global is defined on the C++ side too, but
         # only if its type is basic or string (see ROOT.py).
         # The new PyROOT will discontinue this feature.

         # Note that in the new PyROOT we can still define a
         # global in C++ and access/modify it from Python
         ROOT.gInterpreter.Declare("int gMyOwnGlobal2 = 1;")
         self.assertEqual(ROOT.gMyOwnGlobal2, 1)
         ROOT.gMyOwnGlobal2 = -1
         self.assert_(gROOT.ProcessLine('gMyOwnGlobal2 == -1'))

   def test4AutoLoading( self ):
      """Test auto-loading by retrieving a non-preloaded class"""

      t = TLorentzVector()
      self.failUnless( isinstance( t, TLorentzVector ) )

   def test5MacroLoading( self ):
      """Test accessibility to macro classes"""
      gROOT.LoadMacro( 'SimpleClass.C' )

      self.assert_( issubclass( ROOT.SimpleClass, ROOT.TheBase ) )
      self.assertEqual( ROOT.SimpleClass, ROOT.SimpleClass_t )

      c = ROOT.SimpleClass()
      self.failUnless( isinstance( c, ROOT.SimpleClass ) )
      self.assertEqual( c.fData, c.GetData() )

      c.SetData( 13 )
      self.assertEqual( c.fData, 13 )
      self.assertEqual( c.GetData(), 13 )


### basic python language features test cases ================================
class Basic3PythonLanguageTestCase( MyTestCase ):
   def test1HaveDocString( self ):
      """Test doc strings existence"""

      self.assert_( hasattr( TCanvas, "__doc__" ) )
      self.assert_( hasattr( TCanvas.__init__, "__doc__" ) )

   def test2BoundUnboundMethodCalls( self ):
      """Test (un)bound method calls"""

      self.assertRaises( TypeError, TLorentzVector.X )

      m = TLorentzVector.X
      self.assertRaises( TypeError, m )
      self.assertRaises( TypeError, m, 1 )

      b = TLorentzVector()
      b.SetX( 1.0 )
      self.assertEqual( 1.0, m( b ) )

   def test3ThreadingSupport( self ):
      """Test whether the GIL can be properly released"""

      try:
         gROOT.GetVersion._threaded = 1
      except AttributeError:
         # Attribute name change in new Cppyy
         gROOT.GetVersion.__release_gil__ = 1

      gROOT.GetVersion()

   def test4ClassAndTypedefEquality( self ):
      """Typedefs of the same class must point to the same python class"""

      gInterpreter.Declare( """namespace PyABC {
         struct SomeStruct {};
         struct SomeOtherStruct {
            typedef std::vector<const PyABC::SomeStruct*> StructContainer;
         };
      }""" )

      import cppyy
      PyABC = cppyy.gbl.PyABC

      self.assert_( PyABC.SomeOtherStruct.StructContainer is cppyy.gbl.std.vector('const PyABC::SomeStruct*') )


### basic C++ argument basic (value/ref and compiled/interpreted) ============
class Basic4ArgumentPassingTestCase( MyTestCase ):
   def test1TStringByValueInterpreted( self ):
      """Test passing a TString by value through an interpreted function"""

      gROOT.LoadMacro( 'ArgumentPassingInterpreted.C' )

      f = ROOT.InterpretedTest.StringValueArguments

      self.assertEqual( f( 'aap' ), 'aap' )
      self.assertEqual( f( TString( 'noot' ) ), 'noot' )
      self.assertEqual( f( 'zus', 1, 'default' ), 'default' )
      self.assertEqual( f( 'zus', 1 ), 'default' )
      self.assertEqual( f( 'jet', 1, TString( 'teun' ) ), 'teun' )

   def test2TStringByRefInterpreted( self ):
      """Test passing a TString by reference through an interpreted function"""

      # script ArgumentPassingInterpreted.C already loaded in by value test

      f = ROOT.InterpretedTest.StringRefArguments

      self.assertEqual( f( 'aap' ), 'aap' )
      self.assertEqual( f( TString( 'noot' ) ), 'noot' )
      self.assertEqual( f( 'zus', 1, 'default' ), 'default' )
      self.assertEqual( f( 'zus', 1 ), 'default' )
      self.assertEqual( f( 'jet', 1, TString( 'teun' ) ), 'teun' )

   def test3TLorentzVectorByValueInterpreted( self ):
      """Test passing a TLorentzVector by value through an interpreted function"""

      # script ArgumentPassingInterpreted.C already loaded in by value test

      f = ROOT.InterpretedTest.LorentzVectorValueArguments

      self.assertEqual( f( TLorentzVector( 5, 6, 7, 8 ) ), TLorentzVector( 5, 6, 7, 8 ) )
      self.assertEqual( f( TLorentzVector(), 1 ), TLorentzVector( 1, 2, 3, 4 ) )

   def test4TLorentzVectorByRefInterpreted( self ):
      """Test passing a TLorentzVector by reference through an interpreted function"""

      # script ArgumentPassingInterpreted.C already loaded in by value test

      f = ROOT.InterpretedTest.LorentzVectorRefArguments

      self.assertEqual( f( TLorentzVector( 5, 6, 7, 8 ) ), TLorentzVector( 5, 6, 7, 8 ) )
      self.assertEqual( f( TLorentzVector(), 1 ), TLorentzVector( 1, 2, 3, 4 ) )

   def test5TStringByValueCompiled( self ):
      """Test passing a TString by value through a compiled function"""

      gROOT.LoadMacro( 'ArgumentPassingCompiled.C++' )

      f = ROOT.CompiledTest.StringValueArguments

      self.assertEqual( f( 'aap' ), 'aap' )
      self.assertEqual( f( TString( 'noot' ) ), 'noot' )
      self.assertEqual( f( 'zus', 1, 'default' ), 'default' )
      self.assertEqual( f( 'zus', 1 ), 'default' )
      self.assertEqual( f( 'jet', 1, TString( 'teun' ) ), 'teun' )

   def test6TStringByRefCompiled( self ):
      """Test passing a TString by reference through a compiled function"""

      # script ArgumentPassingCompiled.C already loaded in by value test

      f = ROOT.CompiledTest.StringRefArguments

      self.assertEqual( f( 'aap' ), 'aap' )
      self.assertEqual( f( TString( 'noot' ) ), 'noot' )
      self.assertEqual( f( 'zus', 1, 'default' ), 'default' )
      self.assertEqual( f( 'zus', 1 ), 'default' )
      self.assertEqual( f( 'jet', 1, TString( 'teun' ) ), 'teun' )

   def test7TLorentzVectorByValueCompiled( self ):
      """Test passing a TLorentzVector by value through a compiled function"""

      # script ArgumentPassingCompiled.C already loaded in by value test

      f = ROOT.CompiledTest.LorentzVectorValueArguments

      self.assertEqual( f( TLorentzVector( 5, 6, 7, 8 ) ), TLorentzVector( 5, 6, 7, 8 ) )
      self.assertEqual( f( TLorentzVector(), 1 ), TLorentzVector( 1, 2, 3, 4 ) )

   def test8TLorentzVectorByRefCompiled( self ):
      """Test passing a TLorentzVector by reference through a compiled function"""

      # script ArgumentPassingCompiled.C already loaded in by value test

      f = ROOT.CompiledTest.LorentzVectorRefArguments

      self.assertEqual( f( TLorentzVector( 5, 6, 7, 8 ) ), TLorentzVector( 5, 6, 7, 8 ) )
      self.assertEqual( f( TLorentzVector(), 1 ), TLorentzVector( 1, 2, 3, 4 ) )

   def test9ByRefPassing( self ):
      """Test passing by-reference of builtin types"""

      import array, sys

      if 'linux' in sys.platform:
         a = array.array('I',[0])
         val = ROOT.CompiledTest.UnsignedIntByRef( a )
         self.assertEqual( a[0], val )


### basic extension features test cases ======================================
class Basic5PythonizationTestCase( MyTestCase ):
   def test1Strings( self ):
      """Test string/TString/TObjString compatibility"""

      pyteststr = "aap noot mies"

      s1 = TString( pyteststr )
      s2 = str( s1 )

      self.assertEqual( s1, s2 )

      s3 = TObjString( s2 )
      self.assertEqual( s2, s3 )
      self.assertEqual( s2, pyteststr )

   def test2Lists( self ):
      """Test list/TList behavior and compatibility"""

      l = TList()
      l.Add( TObjString('a') )
      l.Add( TObjString('b') )
      l.Add( TObjString('c') )
      l.Add( TObjString('d') )
      l.Add( TObjString('e') )
      l.Add( TObjString('f') )
      l.Add( TObjString('g') )
      l.Add( TObjString('h') )
      l.Add( TObjString('i') )
      l.Add( TObjString('j') )

      self.assertEqual( len(l), 10 )
      self.assertEqual( l[3], 'd' )
      self.assertEqual( l[-1], 'j' )
      self.assertRaises( IndexError, l.__getitem__,  20 )
      self.assertRaises( IndexError, l.__getitem__, -20 )

      self.assertEqual( list(l), ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'] )

      l[3] = TObjString('z')
      self.assertEqual( list(l), ['a', 'b', 'c', 'z', 'e', 'f', 'g', 'h', 'i', 'j'] )

      del l[2]
      self.assertEqual( list(l), ['a', 'b', 'z', 'e', 'f', 'g', 'h', 'i', 'j'] )

      self.assert_( TObjString('b') in l )
      self.assert_( not TObjString('x') in l )

      self.assertEqual( list(l[2:6]),   ['z', 'e', 'f', 'g'] )
      self.assertEqual( list(l[2:6:2]), ['z', 'f'] )
      self.assertEqual( list(l[-5:-2]), ['f', 'g', 'h'] )
      self.assertEqual( list(l[7:]),    ['i', 'j'] )
      self.assertEqual( list(l[:3]),    ['a', 'b', 'z'] )

      del l[2:4]
      self.assertEqual( list(l), ['a', 'b', 'f', 'g', 'h', 'i', 'j'] )

      l[2:5] = [ TObjString('1'), TObjString('2') ]
      self.assertEqual( list(l), ['a', 'b', '1', '2', 'i', 'j'] )

      l[6:6] = [ TObjString('3') ]
      self.assertEqual( list(l), ['a', 'b', '1', '2', 'i', 'j', '3'] )

      l.append( TObjString('4') )
      self.assertEqual( list(l), ['a', 'b', '1', '2', 'i', 'j', '3', '4'] )

      l.extend( [ TObjString('5'), TObjString('j') ] )
      self.assertEqual( list(l), ['a', 'b', '1', '2', 'i', 'j', '3', '4', '5', 'j'] )
      self.assertEqual( l.count( 'b' ), 1 )
      self.assertEqual( l.count( 'j' ), 2 )
      self.assertEqual( l.count( 'x' ), 0 )

      self.assertEqual( l.index( TObjString( 'i' ) ), 4 )
      self.assertRaises( ValueError, l.index, TObjString( 'x' ) )

      l.insert(  3, TObjString('6') )
      l.insert( 20, TObjString('7') )
      l.insert( -1, TObjString('8') )
      self.assertEqual( list(l), ['8', 'a', 'b', '1', '6', '2', 'i', 'j', '3', '4', '5', 'j', '7'] )
      self.assertEqual( l.pop(), '7' )
      self.assertEqual( l.pop(3), '1' )
      self.assertEqual( list(l), ['8', 'a', 'b', '6', '2', 'i', 'j', '3', '4', '5', 'j'] )

      l.remove( TObjString( 'j' ) )
      l.remove( TObjString( '3' ) )

      self.assertRaises( ValueError, l.remove, TObjString( 'x' ) )
      self.assertEqual( list(l), ['8', 'a', 'b', '6', '2', 'i', '4', '5', 'j'] )

      l.reverse()
      self.assertEqual( list(l), ['j', '5', '4', 'i', '2', '6', 'b', 'a', '8'] )

      l.sort()
      self.assertEqual( list(l), ['2', '4', '5', '6', '8', 'a', 'b', 'i', 'j'] )

      if sys.hexversion >= 0x3000000:
         l.sort( key=TObjString.GetName )
         l.reverse()
      else:
         l.sort( lambda a, b: cmp(b.GetName(),a.GetName()) )
      self.assertEqual( list(l), ['j', 'i', 'b', 'a', '8', '6', '5', '4', '2'] )

      l2 = l[:3]
      self.assertEqual( list(l2 * 3), ['j', 'i', 'b', 'j', 'i', 'b', 'j', 'i', 'b'] )
      self.assertEqual( list(3 * l2), ['j', 'i', 'b', 'j', 'i', 'b', 'j', 'i', 'b'] )

      l2 *= 3
      self.assertEqual( list(l2), ['j', 'i', 'b', 'j', 'i', 'b', 'j', 'i', 'b'] )

      l2 = l[:3]
      l3 = l[6:8]
      self.assertEqual( list(l2+l3), ['j', 'i', 'b', '5', '4'] )

      if sys.hexversion >= 0x3000000:
         next = '__next__'
      else:
         next = 'next'
      i = iter(l2)
      self.assertEqual( getattr( i, next )(), 'j' )
      self.assertEqual( getattr( i, next )(), 'i' )
      self.assertEqual( getattr( i, next )(), 'b' )
      self.assertRaises( StopIteration, getattr( i, next ) )

   def test3TVector( self ):
      """Test TVector2/3/T behavior"""

      import math

      N = 51

    # TVectorF is a typedef of floats
      v = TVectorF(N)
      for i in range( N ):
          v[i] = i*i

      for j in v:
         self.assertEqual( round( v[ int(math.sqrt(j)+0.5) ] - j, 5 ), 0 )

   def test4TObjArray( self ):
      """Test TObjArray iterator-based copying"""

      a = TObjArray()
      b = list( a )

      self.assertEqual( b, [] )

   def test5Hashing( self ):
      """C++ objects must be hashable"""

      a = TH1D("asd", "asd", 10, 0, 1)
      self.assert_( hash(a) )

### basic C++ return integer types  ============
class Basic6ReturnValueTestCase( MyTestCase ):
   def test1ReturnIntegers( self ):
      """Test returning all sort of interger types"""

      gROOT.LoadMacro( 'ReturnValues.C' )

      tests = ROOT.testIntegerResults()
      for type in ["short", "int", "long", "longlong"]:
        for name, value in [("PlusOne", 1), ("MinusOne", -1)]:
          member = "%s%s" % (type, name)
          result = getattr(tests, member)()
          self.assertEqual(result, value , '%s() == %s, should be %s' % (member, result, value))


## actual test run
if __name__ == '__main__':
   #import common
   result = run_pytest(__file__)
   sys.exit(result)

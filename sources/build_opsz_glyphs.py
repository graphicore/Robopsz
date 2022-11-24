#! /usr/bin/env python
import sys
from fontTools.designspaceLib import DesignSpaceDocument, RuleDescriptor
from fontTools.ufoLib import UFOWriter
from fontTools.ufoLib.glifLib import Glyph
from functools import partial

numberToGlyphName = [
   'zero'
  ,'one'
  ,'two'
  ,'three'
  ,'four'
  ,'five'
  ,'six'
  ,'seven'
  ,'eight'
  ,'nine'
]


def _readGlyph(glyphSet, glyphName):
  glyph = glyphSet[glyphName]
  glyphSet.readGlyph(glyphName, glyph)
  return glyph

def opszGlyphName(intPart, fracPart):
  return f'opsz.{intPart}_{fracPart}'

def glyphNamesFromNumber(integer):
  return [numberToGlyphName[int(i)] for i in list(str(integer))]


def _componentsToPen(components, componentAdvances, pen):
  advance = 0
  for componentName in components:
    # translate transformation (1, 0, 0, 1, x, y)
    pen.addComponent(componentName, (1, 0, 0, 1, advance, 0))
    advance += componentAdvances[componentName]

def createOPSZGlyph(glyphSet, componentAdvances, intPart, fracPart):
  glyphName = opszGlyphName(intPart, fracPart)
  glyph = Glyph(glyphName, glyphSet)
  components = glyphNamesFromNumber(intPart) + ['period'] + glyphNamesFromNumber(fracPart);
  advance = 0
  for componentName in components:
    advance += componentAdvances[componentName]
  glyph.width = advance
  drawPointsFunc = partial(_componentsToPen, components, componentAdvances)
  print('writeGlyph', glyphName, 'with:', *components)
  glyphSet.writeGlyph(glyphName, glyph, drawPointsFunc)

def main(designspacePath):
  doc = DesignSpaceDocument.fromfile(designspacePath)
  for source in doc.sources:
    print(f'Source {source.path}:')
    ufo = UFOWriter(source.path)
    glyphSet = ufo.getGlyphSet()
    componentAdvances = dict()
    componentAdvances['period'] = _readGlyph(glyphSet, 'period').width;
    for i in range(10):
      glyphName = numberToGlyphName[i]
      componentAdvances[glyphName] = _readGlyph(glyphSet, glyphName).width;
    for intPart in range(8, 145):
      for fracPart in range(10):
        createOPSZGlyph(glyphSet, componentAdvances, intPart, fracPart)
    glyphSet.writeContents();
    ufo.writeLayerContents();

  rules = []
  for intPart in range(8, 145):
    for fracPart in range(10):
      frac = fracPart/10
      rule = RuleDescriptor(
        name=f'opsz{intPart}_{fracPart}',
        conditionSets=[[{'minimum': intPart + frac, 'maximum': intPart + frac + .099, 'name': 'opsz'}]],
        subs=[('underscore', opszGlyphName(intPart, fracPart))],
      )
      rules.append(rule)
  doc.rules = rules
  doc.write(path=doc.path)


if __name__ == '__main__':
  try:
    designspacePath = sys.argv[1]
  except IndexError:
    print(f'Please provide .designspace file location.')
    print(f'Usage:\n    {sys.argv[0]} some/path/to/my.designspace')
    sys.exit(1);
  main(designspacePath)

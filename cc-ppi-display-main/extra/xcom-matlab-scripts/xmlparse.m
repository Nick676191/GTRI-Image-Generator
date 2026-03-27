function S = xmlparse(xmlfile)
%XMLPARSE   Parse XML file into XMLELEM tree
%   TREE = XMLPARSE('xmlfile') parses an XML file specified by the string
%   'xmlfile', constructs an XMLELEM tree, and returns the root XMLELEM
%   object.
%
%   Example:
%      % Parse XML file to XMLELEM tree
%      T = xmlparse(fullfile(matlabroot,'toolbox','matlab','general','info.xml'))
%
%      % Flatten the tree
%      F = xmlfind(T)
%
%      % Find XML element text with 'matlab'
%      elem = xmlfind(T,'Name','#text','Value','matlab')
%
%   See Also: XMLELEM, XMLFIND.

% Copyright 2012 Takeshi Ikuma
% History:
% rev. - : (05-11-2012) original release

try
   xDoc = xmlread(xmlfile);
catch ME
   %ME.rethrowAsCaller();
   throwAsCaller (ME);
end
S = traversenodes(xDoc.getFirstChild(),xmlelem.empty);

end

function [S,empty] = traversenodes(node,parent)

S = createnodeobj(node,parent);

nodes = node.getChildNodes();
N = nodes.getLength();
Idel = false(1,N);
for i=0:N-1
   [S.Children(i+1),Idel(i+1)] = traversenodes(nodes.item(i),S);
end
S.Children(Idel) = [];

empty = S.isemptytext() && N==0;

end

function S = createnodeobj(node,parent)

S = xmlelem(char(node.getNodeName),char(node.getNodeValue),parent);

attrs = node.getAttributes();
if ~isempty(attrs)
   for i = 0:attrs.getLength()-1
      attr = attrs.item(i);
      name = char(attr.getName());
      S.addprop(name);
      S.(name) = char(attr.getValue());
   end
end
end
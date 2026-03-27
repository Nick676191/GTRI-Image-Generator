function nodes = xmlfind(S,varargin)
%XMLFIND Find XML elements with specified property values.
%   ELEMS = XMLFIND(XmlElements,'P1Name',P1Value,...) returns the handles
%   of the XMLELEM objects listed in XmlElements and below whose property
%   values match those passed as param-value pairs to the XMLFIND command.
%
%   ELEMS = XMLFIND(XmlElements, 'flat', 'P1Name', P1Value,...) restricts
%   the search only to the objects listed in XmlElements.  Their
%   descendents are not searched.
%
%   ELEMS = XMLFIND(XmlElements, '-depth', d,...) specifies the depth of
%   the search. It controls how many levels under the handles in
%   XmlElements are traversed. Specifying d=0 gets the same behavior as
%   using the 'flat' argument. Specifying d=inf gets the default behavior
%   of all levels.
%
%   ELEMS = XMLFIND(XmlElements) returns the XMLELEM objects listed in
%   XmlElements, and the XMLELEM objects of all their descendents.
%
%   ELEMS = XMLFIND(XmlElements,'P1Name', P1Value, '-logicaloperator', ...)
%   applies the logical operator to the property value matching. Possible
%   values for -logicaloperator are -and, -or, -xor, -not.
%
%   ELEMS = XMLFIND(XmlElements,'-regexp', 'P1Name', 'regexp',...) matches
%   objects using regular expressions as if the value of the property
%   P1Name is passed to REGEXP as: regexp(PropertyValue, 'regexp'). XMLFIND
%   returns the XMLELEM object if a match occurs.
%
%   ELEMS = XMLFIND(XmlElements,'-property', 'P1Name') finds all XML
%   Elements having the specified property.
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
%   See also XMLPARSE, XMLELEM.

% Copyright 2012 Takeshi Ikuma
% History:
% rev. - : (05-11-2012) original release


[argfindobj,depth] = parse_input(varargin);
nodes = traverse_nodes(S,argfindobj,depth);

end

function nodes = traverse_nodes(S,argfindobj,depth)

nodes = findobj(S,argfindobj{:});
if depth>0 && ~isempty(S)
   cnodes = [S.Children];
   nodes = [nodes;traverse_nodes(cnodes,argfindobj,depth-1)];
end
end

function [argfindobj,depth] = parse_input(argin)

Narg = numel(argin);
argfindobj = {};
depth = inf; % negative -> all levels

if isempty(argin), return; end

% check for the depth option
if ~ischar(argin{1}) || size(argin{1},1)~=1
   error('Property name must be a string of characters.');
end
name = argin{1};
if strcmpi(name,'flat')
   depth = 0;
   i = 2;  % argument index
elseif strcmpi(name,'-depth')
   if Narg<2
      error('Depth option requires a non-negative integer to specify the depth of the search.');
   end
   val = argin{2};
   if Narg<2 || ~isnumeric(val) || numel(val)~=1 || isnan(val) || val<0 || val~=floor(val)
      error('Depth must be given as a non-negative integer.');
   end
   depth = argin{2};
   if depth<0, depth = inf; end
   i = 3;  % argument index
else
   i = 1;  % argument index
end
argfindobj = argin(i:end);

end
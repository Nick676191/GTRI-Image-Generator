classdef xmlelem < dynamicprops
   %XMLELEM   XML element class
   %   XMLELEM class is a handle class with dynamic properties to store XML
   %   element information. Attributes of each XML element are stored as a
   %   property.
   %
   %XMLELEM Static Properties:
   %   Name     - Tag Name (or '#text' if it holds element text)
   %   Value    - (Typically) element text string
   %   Parent   - Parent XMLELEM object
   %   Children - Array of children XMLELEM objects
   %
   %XMLELEM Methods:
   %   XMLELEM - Constructor
   %   ISEMPTYTEXT - true if it is an empty string
   %
   %   See also: XMLPARSE, XMLFIND.
   
   % Copyright 2012 Takeshi Ikuma
   % History:
   % rev. - : (05-11-2012) original release
   
   properties
      Name
      Value
      Parent
      Children
   end
   methods
      function obj = xmlelem(name,value,parent)
         %XMLELEM/XMLELEM   Constructs XML node object
         %   XMLELEM('Name',Value,Parent) 
         
         if nargin==0
            obj.Name = '';
            obj.Value = '';
         else
            obj.Name = name;
            obj.Value = deblank(value);
         end
         
         obj.Parent = parent;
         obj.Children = xmlelem.empty;
      end
      
      function empty = isemptytext(obj)
         %XMLELEM/ISEMPTYTEXT   Returns true if empty text
%         empty = arrayfun(@(o)(strcmp(o.Name,'#text') && isempty(o.Value)),obj);    %-- for versions of MATLAB 2010b and later
         empty = (strcmp(obj.Name,'#text') && isempty(obj.Value));                 %-- for versions of MATLAB prior to 2010b
      end
   end
end
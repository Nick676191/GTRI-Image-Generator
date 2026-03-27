classdef (Sealed) xdatfile < handle
%-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
%-- classdef xdatfile
%--
%-- Provides properties and methods to dynamically access X-Com Systems
%-- XDAT files.
%--
%-- Properties:
%--     CenterFrequency                     %-- Center frequency of collection.
%--     MarkerCount                         %-- Number of markers in collection.
%--     SampleCount                         %-- Number of samples in collection.
%--     SampleRate                          %-- Sample rate of collection.
%--     ScaleFactor                         %-- Scale factor of collection.
%--     Span                                %-- Frequency span of collection.
%--     StartTime                           %-- Start time of collection.
%--
%-- Constructor:
%--     xdatfile (basefilename)             %-- Instantiates the xdatfile and retrieves property values.
%--
%-- Methods:
%--     SamplesIQ (varargin)                %-- Returns integer I & Q samples along with markers matching the requested samples.
%--     ComplexIQ (varargin)                %-- Returns complex I & Q samples along with markers matching the requested samples.
%--     VoltsIQ (varargin)                  %-- Returns complex I & Q samples converted to volts along with markers matching the requested samples.
%--     Markers                             %-- Returns markers.
%--     rewind (varargin)                   %-- Rewinds the file pointer the requested number of samples or to the beginning of the file.
%--     fastfwd (varargin)                  %-- Fast forwards the file pointer the requested number of samples or to the end of the file.
%--     fileptr (varargin)                  %-- Moves the file pointer to the requested sample and/or returns the current file pointer sample number. 
%--
%-- Usage Examples:
%--    xdf = xdatfile ('basefilename');
%--
%--    [I, Q, M] = xdf.SamplesIQ;           %-- Returns all samples in integer format and markers.
%--    [I, Q, M] = xdf.SamplesIQ (N);       %-- Returns the next N samples in integer format from the current file position along with markers matching the requested samples.
%--    [I, Q, M] = xdf.SamplesIQ (X, Y);    %-- Returns samples X through Y in integer format along with markers matching the requested samples.
%--
%--    [CIQ, M] = xdf.ComplexIQ;            %-- Returns all samples in complex format and markers.
%--    [CIQ, M] = xdf.ComplexIQ (N);        %-- Returns the next N samples in complex format from the current file position along with markers matching the requested samples.
%--    [CIQ, M] = xdf.ComplexIQ (X, Y);     %-- Returns samples X through Y in complex format along with markers matching the requested samples.
%--
%--    [VIQ, M] = xdf.VoltsIQ;              %-- Returns all samples in complex volts format and markers.
%--    [VIQ, M] = xdf.VoltsIQ (N);          %-- Returns the next N samples in complex volts format from the current file position along with markers matching the requested samples.
%--    [VIQ, M] = xdf.VoltsIQ (X, Y);       %-- Returns samples X through Y in complex votls format along with markers matching the requested samples.
%--
%--     M = xdf.Markers;                    %-- Returns all markers
%-- 
%--     xdf.rewind;                         %-- Reset file pointer to beginning of file.
%--     xdf.rewind (N);                     %-- Rewinds the file pointer N samples.
%--
%--     xdf.fastfwd;                        %-- Fast fowards the file pointer to the end of the file.
%--     xdf.fastfwd (N);                    %-- Fast fowards the file pointer N samples.
%--
%--     S = xdf.fileptr;                    %-- Returns the current file pointer sample number.
%--     S = xdf.fileptr (N);                %-- Moves the file pointer to sample N and returns the new file pointer sample number.
%--
%--     xdf.<property name>                 %-- Returns value of <property name>.
%-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	properties (Hidden)
		hdrfilename
		mkrfilename
		datfilename
        filepos
        markers
	end
	properties (SetAccess = private)
		CenterFrequency             %-- Center frequency of collection
        MarkerCount                 %-- Number of markers
        SampleCount                 %-- Number of samples 
        SampleRate                  %-- Sample rate of collection
		ScaleFactor                 %-- Scale factor of collection
		Span                        %-- Frequency span of collection
		StartTime                   %-- Start time of collection
	end
	methods
		function XDF = xdatfile (basefilename)
        %-- Instantiate xdatfile, parse header
			%-- Initialize filenames and file position.
			XDF.hdrfilename = strcat (basefilename, '.xhdr');
            XDF.mkrfilename = strcat (basefilename, '.xmrk');
            if (exist (XDF.mkrfilename) == 0)
                XDF.mkrfilename = strcat (basefilename, '.xdat.xmrk');
            end
            XDF.datfilename = strcat (basefilename, '.xdat');
            XDF.filepos     = 0;
            XDF.MarkerCount = 0;
            XDF.SampleCount = 0;

            %-- Parse the header file and read the variables that we support
            HDR = xmlparse (XDF.hdrfilename);
            for i = 1:length (HDR.Children)
                if (strcmp ('captures', HDR.Children (i).Name))
                    XDF.CenterFrequency = str2num (HDR.Children (i).Children.center_frequency);
                    XDF.SampleRate      = str2num (HDR.Children (i).Children.sample_rate);
                    if (length (findobj (HDR.Children (i).Children, '-property', 'acq_scale_factor')) > 0)
                        XDF.ScaleFactor = str2num (HDR.Children (i).Children.acq_scale_factor);
                    elseif (length (findobj (HDR.Children (i).Children, '-property', 'scale_factor')) > 0)
                        XDF.ScaleFactor = str2num (HDR.Children (i).Children.scale_factor);
                    end
                    if (length (findobj (HDR.Children (i).Children, '-property', 'acquisition_bandwidth')) > 0)
                        XDF.Span        = str2num (HDR.Children (i).Children.acquisition_bandwidth);
                    elseif (length (findobj (HDR.Children (i).Children, '-property', 'span')) > 0)
                         XDF.Span       = str2num (HDR.Children (i).Children.span);
                    end
                    XDF.StartTime       = HDR.Children (i).Children.start_capture;
                end
                if (strcmp ('data_files', HDR.Children(i).Name))
                    XDF.SampleCount = str2num (HDR.Children (i).Children.samples);
                end
                if (strcmp ('marker_files', HDR.Children(i).Name) && length (HDR.Children(i).Children > 0))
                    XDF.MarkerCount = str2num (HDR.Children (i).Children.count);
                end
            end
            
            if (XDF.MarkerCount > 0) && (exist (XDF.mkrfilename))
                x = xmlparse (XDF.mkrfilename);
                x = x.Children;
                y = fields (x (1));
                for i = 1:XDF.MarkerCount
                    for j = 5:length (y)
                        str = sprintf ('markers (i).%s = x (i).%s;', y {j}, y {j});
                        eval (str);
                        if ((length (strfind (y {j}, 'sample')) > 0) || (length( strfind (y {j}, 'number')) > 0))
                            str = sprintf ('markers (i).%s = int64 (str2num (markers (i).%s));', y {j}, y {j});
                            eval (str);
                        end
                    end
                end
                XDF.markers = markers;
            end
        end
        
        function rewind (obj, varargin)
            switch (length (varargin))
                %-- Reset file pointer to beginning of file
                case 0  
                    obj.filepos = 0;
                    
                %-- Rewind varargin {1} samples - if this puts us before the begining of the file, then go to sample 0
                case 1
                    num_samples = varargin {1};
                    if ((obj.filepos - (num_samples * 4)) < 0)
                        obj.filepos = 0;
                    else
                        obj.filepos = obj.filepos - (num_samples * 4);
                    end
            end
        end
        
        function fastfwd (obj, varargin)
            switch (length (varargin))
                %-- Reset file pointer to end of file
                case 0  
                    obj.filepos = obj.SampleCount * 4;
                    
                %-- Fast forward varargin {1} samples - if this puts us past the end of the file, then go to the end of the file
                case 1
                    num_samples = varargin {1};
                    if ((obj.filepos - (num_samples * 4)) > (obj.SampleCount * 4))
                        obj.filepos = obj.SampleCount * 4;
                    else
                        obj.filepos = obj.filepos + (num_samples * 4);
                    end
            end
        end
        
        function samplenumber = fileptr (obj, varargin)
            samplenumber = NaN;
             switch (length (varargin))
                 case 0
                     samplenumber = obj.filepos / 4;
                 case 1
                     sample_num = varargin {1};
                     if ((sample_num >= 0) && (sample_num <= obj.SampleCount))
                         obj.filepos = sample_num * 4;
                     elseif (sample_num < 0)
                         obj.filepos = 0;
                     elseif (sample_num > obj.SampleCount)
                         obj.filepos = obj.SampleCount * 4;
                     end
                     samplenumber = obj.filepos / 4;
             end
        end
        
        function varargout = SamplesIQ (obj, varargin)
        %-- Retreives specified IQ samples in integer format along with markers matching the requested set of samples.
        infile = fopen (obj.datfilename);
            if (infile < 0)
                ME = MException ('MATLAB:fopen:FileNotFound', 'File %s not found', obj.datfilename);
                throwAsCaller (ME);
            end
            
            switch (length (varargin))
                %-- Read all samples
                case 0  
                    disp ('Reading all samples...');
                    fseek (infile, 0, 'bof');
                    data = fread (infile, 'uint32', 'b');
                    
                    marker_1 = 1;
                    marker_n = obj.MarkerCount;
                    
                %-- Read next N samples from current file position
                case 1  
                    disp (sprintf ('Reading %d samples from current file sample position %d', varargin {1}, (obj.filepos + 4)/4));
                    fseek (infile, obj.filepos, 'bof');
                    data = fread (infile, varargin {1}, 'uint32', 'b');
                    
                    marker_1 = 0;
                    marker_n = 0;
                    
                    if (obj.MarkerCount > 0)
                        start = ((obj.filepos + 4)/4);
                        stop  = (((obj.filepos + 4)/4) + varargin {1});
                        if (isfield (obj.markers, 'absolute_sample_number'))
                            x = find (cellfun (@(x) (x >= start) && (x <= stop), {obj.markers.absolute_sample_number}));
                        elseif (isfield (obj.markers, 'file_sample_number'))
                            x = find (cellfun (@(x) (x >= start) && (x <= stop), {obj.markers.file_sample_number}));
                        else
                            x = [];
                        end
                        if (numel (x) > 0)
                            marker_1 = x (1);
                            marker_n = x (length (x));
                        end
                    end
                    
                %-- Read specified range of samples (n. m)
                case 2  
                    disp (sprintf ('Reading %d samples beginning at sample %d', varargin {2} - varargin {1} + 1, varargin {1}));
                    fseek (infile, (varargin {1} - 1)*4, 'bof');
                    data = fread (infile, varargin {2} - varargin {1} + 1, 'uint32', 'b');
                    
                    marker_1 = 0;
                    marker_n = 0;
                    
                    if (obj.MarkerCount > 0)
                        start = (varargin {1} - 1);
                        stop  = (varargin {2} - 1);
                        if (isfield (obj.markers, 'absolute_sample_number'))
                            x = find (cellfun (@(x) (x >= start) && (x <= stop), {obj.markers.absolute_sample_number}));
                        elseif (isfield (obj.markers, 'file_sample_number'))
                            x = find (cellfun (@(x) (x >= start) && (x <= stop), {obj.markers.file_sample_number}));
                        else
                            x = [];
                        end
                        if (numel (x) > 0)
                            marker_1 = x (1);
                            marker_n = x (length (x));
                        end
                    end
            end
            
            varargout {1} = bitshift (data, -16);
            varargout {2} = bitand   (data, 65535);

            varargout {1} = swapbytes (uint16 (varargout {1}));
            varargout {2} = swapbytes (uint16 (varargout {2}));

            varargout {1} = typecast (uint16 (varargout {1}), 'int16');
            varargout {2} = typecast (uint16 (varargout {2}), 'int16');
            
            if (marker_1 > 0)
                varargout {3} = obj.markers (marker_1:marker_n);
            else
                varargout {3} = 0;
            end

            obj.filepos = ftell (infile);
            fclose (infile);
        end
        
        function varargout = ComplexIQ (obj, varargin)
        %-- Retreives specified IQ samples in complex format along with markers matching the requested set of samples.            
            infile = fopen (obj.datfilename);
            if (infile < 0)
                ME = MException ('MATLAB:fopen:FileNotFound', 'File %s not found', obj.datfilename);
                throwAsCaller (ME);
            end
            
            switch (length (varargin))
                %-- Read all samples
                case 0  
                    disp ('Reading all samples...');
                    fseek (infile, 0, 'bof');
                    data = fread (infile, 'uint32', 'b');
 
                    marker_1 = 1;
                    marker_n = obj.MarkerCount;

                %-- Read next N samples from current file position
                case 1  
                    disp (sprintf ('Reading %d samples from current file sample position %d\n', varargin {1}, (obj.filepos + 4)/4));
                    fseek (infile, obj.filepos, 'bof');
                    data = fread (infile, varargin {1}, 'uint32', 'b');
                    
                    marker_1 = 0;
                    marker_n = 0;
                    
                    if (obj.MarkerCount > 0)
                        start = ((obj.filepos + 4)/4);
                        stop  = (((obj.filepos + 4)/4) + varargin {1});
                        if (isfield (obj.markers, 'absolute_sample_number'))
                            x = find (cellfun (@(x) (x >= start) && (x <= stop), {obj.markers.absolute_sample_number}));
                        elseif (isfield (obj.markers, 'file_sample_number'))
                            x = find (cellfun (@(x) (x >= start) && (x <= stop), {obj.markers.file_sample_number}));
                        else
                            x = [];
                        end
                        if (numel (x) > 0)
                            marker_1 = x (1);
                            marker_n = x (length (x));
                        end
                    end
                    
                    %-- Read specified range of samples (n. m)
                case 2  
                    disp (sprintf ('Reading %d samples beginning at sample %d', varargin {2} - varargin {1} + 1, varargin {1}));
                    fseek (infile, (varargin {1} - 1)*4, 'bof');
                    data = fread (infile, varargin {2} - varargin {1} + 1, 'uint32', 'b');

                    marker_1 = 0;
                    marker_n = 0;
                    
                    if (obj.MarkerCount > 0)
                        start = (varargin {1} - 1);
                        stop  = (varargin {2} - 1);
                        if (isfield (obj.markers, 'absolute_sample_number'))
                            x = find (cellfun (@(x) (x >= start) && (x <= stop), {obj.markers.absolute_sample_number}));
                        elseif (isfield (obj.markers, 'file_sample_number'))
                            x = find (cellfun (@(x) (x >= start) && (x <= stop), {obj.markers.file_sample_number}));
                        else
                            x = [];
                        end
                        if (numel (x) > 0)
                            marker_1 = x (1);
                            marker_n = x (length (x));
                        end
                    end
            end
            
            I = bitshift (data, -16);
            Q = bitand   (data, 65535);

            I = swapbytes (uint16 (I));
            Q = swapbytes (uint16 (Q));

            I = typecast (uint16 (I), 'int16');
            Q = typecast (uint16 (Q), 'int16');

            obj.filepos = ftell (infile);
            fclose (infile);
            
            varargout {1} = complex (single(I), single(Q));
            if (marker_1 > 0)
                varargout {2} = obj.markers (marker_1:marker_n);
            else
                varargout {2} = 0;
            end
        end 
        
        function varargout = VoltsIQ (obj, varargin)
        %-- Retreives specified IQ samples in complex format along with markers matching the requested set of samples.            
            infile = fopen (obj.datfilename);
            if (infile < 0)
                ME = MException ('MATLAB:fopen:FileNotFound', 'File %s not found', obj.datfilename);
                throwAsCaller (ME);
            end
            
            switch (length (varargin))
                %-- Read all samples
                case 0  
                    disp ('Reading all samples...');
                    fseek (infile, 0, 'bof');
                    data = fread (infile, 'uint32', 'b');
 
                    marker_1 = 1;
                    marker_n = obj.MarkerCount;

                %-- Read next N samples from current file position
                case 1  
                    disp (sprintf ('Reading %d samples from current file sample position %d\n', varargin {1}, (obj.filepos + 4)/4));
                    fseek (infile, obj.filepos, 'bof');
                    data = fread (infile, varargin {1}, 'uint32', 'b');
                    
                    marker_1 = 0;
                    marker_n = 0;
                    
                    if (obj.MarkerCount > 0)
                        start = ((obj.filepos + 4)/4);
                        stop  = (((obj.filepos + 4)/4) + varargin {1});
                        if (isfield (obj.markers, 'absolute_sample_number'))
                            x = find (cellfun (@(x) (x >= start) && (x <= stop), {obj.markers.absolute_sample_number}));
                        elseif (isfield (obj.markers, 'file_sample_number'))
                            x = find (cellfun (@(x) (x >= start) && (x <= stop), {obj.markers.file_sample_number}));
                        else
                            x = [];
                        end
                        if (numel (x) > 0)
                            marker_1 = x (1);
                            marker_n = x (length (x));
                        end
                    end
                    
                    %-- Read specified range of samples (n. m)
                case 2  
                    disp (sprintf ('Reading %d samples beginning at sample %d', varargin {2} - varargin {1} + 1, varargin {1}));
                    fseek (infile, (varargin {1} - 1)*4, 'bof');
                    data = fread (infile, varargin {2} - varargin {1} + 1, 'uint32', 'b');

                    marker_1 = 0;
                    marker_n = 0;
                    
                    if (obj.MarkerCount > 0)
                        start = (varargin {1} - 1);
                        stop  = (varargin {2} - 1);
                        if (isfield (obj.markers, 'absolute_sample_number'))
                            x = find (cellfun (@(x) (x >= start) && (x <= stop), {obj.markers.absolute_sample_number}));
                        elseif (isfield (obj.markers, 'file_sample_number'))
                            x = find (cellfun (@(x) (x >= start) && (x <= stop), {obj.markers.file_sample_number}));
                        else
                            x = [];
                        end
                        if (numel (x) > 0)
                            marker_1 = x (1);
                            marker_n = x (length (x));
                        end
                    end
            end
            
            I = bitshift (data, -16);
            Q = bitand   (data, 65535);

            I = swapbytes (uint16 (I));
            Q = swapbytes (uint16 (Q));

            I = typecast (uint16 (I), 'int16');
            Q = typecast (uint16 (Q), 'int16');
            
            I = single (I) * 65536 * obj.ScaleFactor;
            Q = single (Q) * 65536 * obj.ScaleFactor;
            
            obj.filepos = ftell (infile);
            fclose (infile);
            
            varargout {1} = complex (single(I), single(Q));
            if (marker_1 > 0)
                varargout {2} = obj.markers (marker_1:marker_n);
            else
                varargout {2} = 0;
            end
        end
        
        function M = Markers (obj)
        %-- Retreives all markers
            M = obj.markers;
        end
     
	end %methods	
end %classdef
		
		
		
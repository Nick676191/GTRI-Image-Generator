# import os

# import click
import numpy as np
import pandas as pd


def midas_parser(fp):
    """Main parser function to bring data from a MIDAS BLUE file of
    any type into a usable Python format.

    Arguments:
        fp {str or Path} -- Filepath to MIDAS BLUE data file.

    Returns:
        [tuple] -- (headers, df) contains a dict and a Pandas DataFrame
                   respectively of any header information, if applicable,
                   and then the subsequent data parsed from the binary file.
    """

    # Start the parsing process
    # click.echo(f"PARSING {os.path.basename(fp)}: ")

    # Grab the fixed header
    fix_head = parse_fixed_header(fp=fp)

    # Print out the fixed header key and value pairs
    # click.echo("MIDAS FILE FIXED HEADER: ")
    # for h in range(len(fix_head)):
    # click.echo(f"{fix_head.dtype.names[h]}: {fix_head[h]}\n")

    # Parse the variable/adjunct header based on found midas_type
    var_head = parse_variable_header(fp=fp, fix_head=fix_head)

    # Print the var header key and value pairs
    # click.echo(f"MIDAS FILE TYPE {fix_head['midas_type']} VARIABLE HEADER: ")
    # for h in range(len(var_head)):
    # click.echo(f"{var_head.dtype.names[h]}: {var_head[h]}\n")

    # Parse extended header if there is one
    if fix_head["ext_start"] != 0:

        ext_head = parse_ext_header(fp, fix_head)

        # Print out the contents of the extended header
        # click.echo("MIDAS FILE EXTENDED HEADER: \n")
        # click.echo(f"# of keywords in extended header: {len(ext_head)}\n")

        # for kw in range(len(ext_head)):
        # for h in range(len(ext_head[kw])):
        # click.echo(
        # f"{ext_head[kw].dtype.names[h]}: {ext_head[kw][h]}\n"
        # )

    else:

        ext_head = None

    # Bring headers together
    headers = {"fix": fix_head, "var": var_head, "ext": ext_head}

    # Look for detatched header flag and adjust fp to parse data
    if headers["fix"][3] != 0:
        fp = fp.split(".")[0] + ".det"

    # Use the headers to parse the data
    data_df = parse_data(fp=fp, headers=headers)

    # click.echo(f"MIDAS DATAFRAME: \n {data_df.head(5)}")

    return headers, data_df


def grab_endianness_of_header(fp):
    """Pulls the field that represents the Endianness of the
    bytes that comprise the header in the MIDAS BLUE format.

    Arguments:
        fp {str or Path} -- Filepath

    Returns:
        [str] -- Byte string encoded in latin-1 containing the
                 MIDAS BLUE indication of the header's Endianness
    """
    # Read in the Endianness of the header
    with open(fp, encoding="latin-1") as f:
        rep_header = f.read(8)
        header_endian = rep_header[4:]
        f.close()

    # Define the Endianness char for NumPy dtype obj
    end = determine_np_endianness(byte_endianness=header_endian)

    return end


def parse_fixed_header(fp):
    """Parses the fixed header portion of the MIDAS BLUE binary
    file type. This portion does not change among the different
    versions of the filetype.

    Arguments:
        fp {str or Path} -- Filepath

    Returns:
        [NumPy ndarray] -- Structured array containing all the
                           fields in the fixed header of a
                           MIDAS BLUE file.
    """
    # Define the Endianness char for NumPy dtype obj
    end = grab_endianness_of_header(fp=fp)

    # Classify dtypes of the elements in the fixed header
    ver_d = ("ver", "a4")
    head_rep_d = ("head_rep", "a4")
    data_rep = ("data_rep", "a4")

    detached = ("detached", f"{end}i4")
    protected = ("protected", f"{end}i4")
    pipe = ("pipe", f"{end}i4")

    ext_start = ("ext_start", f"{end}i4")
    ext_size = ("ext_size", f"{end}i4")

    data_start = ("data_start", f"{end}f8")
    data_size = ("data_size", f"{end}f8")
    midas_type = ("midas_type", f"{end}i4")
    data_format = ("data_format", "a2")

    timecode = ("timecode", f"{end}f8")

    inlet = ("inlet", f"{end}i2")
    outlets = ("outlets", f"{end}i2")

    pipeloc = ("pipeloc", f"{end}i4")
    pipesize = ("pipesize", f"{end}i4")

    in_byte = ("in_byte", f"{end}f8")
    out_byte = ("out_byte", f"{end}f8")
    outbytes = ("outbytes", f"8{end}f8")

    keylength = ("keylength", f"{end}i4")
    keywords = ("keywords", (f"{end}a", 92))

    # Define the fixed header labeled NumPy dtype obj
    fix_head_dt_obj = [
        ver_d,
        head_rep_d,
        data_rep,
        detached,
        protected,
        pipe,
        ext_start,
        ext_size,
        data_start,
        data_size,
        midas_type,
        data_format,
        timecode,
        inlet,
        outlets,
        pipeloc,
        pipesize,
        in_byte,
        out_byte,
        outbytes,
        keylength,
        keywords,
    ]

    # Initialize the Numpy dtype obj for fixed header
    fix_head_dt = np.dtype(fix_head_dt_obj)

    # Read in the header from the file given
    fix_head = np.fromfile(file=fp, dtype=fix_head_dt, count=1, offset=0)[0]

    return fix_head


def determine_np_endianness(byte_endianness):
    """Translate's the MIDAS BLUE indication of byte Endianness
    to one that is usable by the NumPy package.

    Arguments:
        byte_endianness {str} -- MIDAS BLUE indication of Endianness.

    Raises:
        ValueError: [description]

    Returns:
        [ValueError] -- ["Error in parsing data representation of MIDAS file.
                        {byte_endianness} not a valid Endian setting.
                        Please use the flags 'big' or 'little'."]
    """
    if byte_endianness == "EEEI":
        np_endian_symb = "<"

    elif byte_endianness == "IEEE":
        np_endian_symb = ">"

    else:
        raise ValueError(
            [
                "Error in parsing data representation of MIDAS file. ",
                f"{byte_endianness} not a valid Endian setting. ",
                "Please use the flags 'big' or 'little'.",
            ]
        )

    return np_endian_symb


def parse_variable_header(fp, fix_head):
    """Given the values of the fixed header, this method calls the
    proper function to parse the variable section of the header that
    changes given the type of MIDAS file fed to it.

    Arguments:
        fp {str or Path} -- Filepath

        fix_head {NumPy ndarray} -- Structured Array containing fixed
                                    header field values.

    Raises:
        ValueError: midas_type parsed as {fix_head['midas_type']}.
                    That type is either unrecognized or not yet supported.

    Returns:
        [NumPy ndarray] -- Structured array containing all the
                           fields in the variable header of a
                           MIDAS BLUE file.
    """
    # Determine the type from the fixed header and call the
    # appropriate parsing method from the header

    # NOTE: Get rid of dependence of the fix_head and just pull
    # the value from the binary file so that this method can
    # be used as a stand-alone.

    if fix_head["midas_type"] == 1000 or fix_head["midas_type"] == 1001:

        var_head = parse_type_1000_var_head(fp=fp)

    elif fix_head["midas_type"] == 2000:

        var_head = parse_type_2000_var_head(fp=fp)

    elif fix_head["midas_type"] == 6000:

        var_head = parse_type_6000_var_head(fp=fp)

    else:

        raise ValueError(
            [
                f"midas_type parsed as {fix_head['midas_type']}. ",
                "That type is either unrecognized or not yet supported.",
            ]
        )

    return var_head


def parse_type_1000_var_head(fp):
    """Parses variable header of MIDAS BLUE type 1000 file.

    Arguments:
        fp {str or Path} -- Filepath

    Returns:
        [NumPy ndarray] -- Structured array containing all the
                           fields in the variable header of a
                           MIDAS BLUE file.
    """
    # Define the byte offset
    var_head_byte_offset = 256

    # Define the Endianness char for NumPy dtype obj
    end = grab_endianness_of_header(fp=fp)

    # Classify dtypes of the elements in the MIDAS 1000 header
    x_start = ("x_start", f"{end}f8")
    x_delta = ("x_delta", f"{end}f8")
    x_units = ("x_units", f"{end}i4")

    # Define the MIDAS 1000 header labeled NumPy dtype obj
    var_head_dt_obj = [x_start, x_delta, x_units]

    # Initialize the Numpy dtype obj for MIDAS 1000 header
    var_head_dt = np.dtype(var_head_dt_obj)

    # Read in the header from the file given
    var_head = np.fromfile(
        file=fp, dtype=var_head_dt, count=1, offset=var_head_byte_offset
    )[0]

    return var_head


def parse_type_2000_var_head(fp):
    """Parses variable header of MIDAS BLUE type 2000 file.

    Arguments:
        fp {str or Path} -- Filepath

    Returns:
        [NumPy ndarray] -- Structured array containing all the
                           fields in the variable header of a
                           MIDAS BLUE file.
    """
    # Define the byte offset
    var_head_byte_offset = 256

    # Define the Endianness char for NumPy dtype obj
    end = grab_endianness_of_header(fp=fp)

    # Classify dtypes of the elements in the MIDAS 2000 header
    x_start = ("x_start", f"{end}f8")  # Frame/column start value
    x_delta = ("x_delta", f"{end}f8")  # Increment between samples in frame
    x_units = ("x_units", f"{end}i4")  # Frame (column) units
    subsize = ("subsize", f"{end}i4")  # Num of data points per frame (row)
    y_start = ("y_start", f"{end}f8")  # Absissa (row) start
    y_delta = ("y_delta", f"{end}f8")  # Increment b/w frames
    y_units = ("y_units", f"{end}i4")  # Absissa (row) unit codef"{end}
    # Define the MIDAS 2000 header labeled NumPy dtype obj
    var_head_dt_obj = [
        x_start,
        x_delta,
        x_units,
        subsize,
        y_start,
        y_delta,
        y_units,
    ]

    # Initialize the Numpy dtype obj for MIDAS 2000 header
    var_head_dt = np.dtype(var_head_dt_obj)

    # Read in the header from the file given
    var_head = np.fromfile(
        file=fp, dtype=var_head_dt, count=1, offset=var_head_byte_offset
    )[0]

    return var_head


def parse_type_6000_var_head(fp):
    """Parses variable header of MIDAS BLUE type 6000 file.

    Arguments:
        fp {str or Path} -- Filepath

    Returns:
        [NumPy ndarray] -- Structured array containing all the
                           fields in the variable header of a
                           MIDAS BLUE file.
    """
    # Define the byte offset
    var_head_byte_offset = 256

    # Define the Endianness char for NumPy dtype obj
    end = grab_endianness_of_header(fp=fp)

    # Classify dtypes of the elements in the MIDAS 6000 header
    r_start = ("r_start", f"{end}f8")  # Abscissa value for 1st record
    r_delta = ("r_delta", f"{end}f8")  # Abscissa value b/w records
    r_units = ("r_units", f"{end}i4")  # Units for record abscissa values

    subrecords = ("subrecords", f"{end}i4")  # Number of cols per record

    r2_start = ("r2_start", f"{end}f8")  # Abscissa value for 1st col record
    r2_delta = ("r2_delta", f"{end}f8")  # Abscissa value b/w record cols
    r2_units = ("r2_units", f"{end}i4")  # Units for col abscissa values

    record_len = ("record_len", f"{end}i4")  # Length of record in bytes

    subrec_struct = (
        "subrec_struct",
        [
            ("name", ("a", 24)),
            ("minval", ("a", 24)),
            ("maxval", ("a", 24)),
            ("offset", ("a", 8)),
            ("num_elts", ("a", 4)),
            ("units", ("a", 4)),
            ("format", ("a", 2)),
            ("uprefix", ("a", 3)),
            ("reserved", ("a", 3)),
        ],
    )  # Individual subrecord structure
    subrecs = ("subrecs", (subrec_struct, 26))  # Total Subrecord structure

    # Define the MIDAS 6000 header labeled NumPy dtype obj
    var_head_dt_obj = [
        r_start,
        r_delta,
        r_units,
        subrecords,
        r2_start,
        r2_delta,
        r2_units,
        record_len,
        subrecs,
    ]

    # Initialize the Numpy dtype obj for MIDAS 6000 header
    var_head_dt = np.dtype(var_head_dt_obj)

    # Read in the header from the file given
    var_head = np.fromfile(
        file=fp, dtype=var_head_dt, count=1, offset=var_head_byte_offset
    )[0]

    return var_head


def parse_ext_header(fp, fix_head):
    """Parses extended header of MIDAS BLUE file.

    Arguments:
        fp {str or Path} -- Filepath

        fix_head {NumPy ndarray} -- Structured array containing
                                    labled values of the MIDAS
                                    fixed header.

    Returns:
        [list] -- List containing structured NumPy arrays
                  that house all the keywords structures
                  in the extended header of a MIDAS BLUE file.
    """
    # Define the Endianness char for NumPy dtype obj
    end = grab_endianness_of_header(fp=fp)

    # Grab the start and end bytes of the extended header
    start_ext = 512 * fix_head["ext_start"]
    num_bytes_ext = fix_head["ext_size"]

    # Construct the const dtype that will be used to help parse kws
    l_key = ("l_key", f"{end}i4")
    l_ext = ("l_ext", f"{end}i2")
    l_tag = ("l_tag", f"{end}i1")
    data_type = ("data_type", (f"{end}a", 1))

    keyword_head_dt_obj = [l_key, l_ext, l_tag, data_type]

    keyword_head_dt = np.dtype(keyword_head_dt_obj)

    # Recursively grab the list of keywords
    def parse_keywords(fp, keyword_lst, kw_start, curr_len, stop_len):
        """Recursive function to pull all keywords from MIDAS BLUE
        extended header.

        Arguments:
            fp {str or Path} -- Filepath
            keyword_lst {list} -- List containing all the ndarrays
                                  that house the keywords
            kw_start {int} -- Byte offset that indicates the start
                              of the extended header.
            curr_len {int} -- Current byte length of the keyword_lst.
            stop_len {int} -- Size of the extended header.

        Returns:
            [list] -- List of structured NumPy ndarrays containing
                      all keywords in a MIDAS BLUE extended header.
        """

        # Grab the keyword header
        kw_head = np.fromfile(
            file=fp, dtype=keyword_head_dt, count=1, offset=kw_start
        )[0]

        # Determine the length and dtype of the value of the kw
        val_len = kw_head["l_key"] - kw_head["l_ext"]
        _, val_type = data_format_code_to_np_designation(
            data_format=kw_head["data_type"]
        )

        # Construct new dtype object based on the parsed value params
        value = ("value", (f"{end}{val_type}", val_len))
        tag = ("tag", ("a", kw_head["l_tag"]))

        keyword_dt_obj = [l_key, l_ext, l_tag, data_type, value, tag]

        keyword_dt = np.dtype(keyword_dt_obj)

        # Parse the keyword given the variable value params and add to
        # the list of keywords
        try:
            kw = np.fromfile(
                file=fp, dtype=keyword_dt, count=1, offset=kw_start
            )[0]

            keyword_lst.append(kw)

        # If we've hit this, it did not parse a full kw, so exit recursion
        except IndexError:
            return keyword_lst

        # Add the length of this keyword to the curr_len
        curr_len += kw["l_key"]
        new_start = kw_start + kw["l_key"]

        # Figure out if we've reached the stop length. If we
        # haven't, call again to add another keyword
        if curr_len < stop_len:

            return parse_keywords(
                fp=fp,
                keyword_lst=keyword_lst,
                kw_start=new_start,
                curr_len=curr_len,
                stop_len=stop_len,
            )

        else:
            return keyword_lst

    # Create a list to hold our keywords and recursively add to it
    keywords = []
    keywords_filled = parse_keywords(
        fp=fp,
        keyword_lst=keywords,
        kw_start=start_ext,
        curr_len=0,
        stop_len=num_bytes_ext,
    )

    return keywords_filled


def parse_data(fp, headers):
    """This is the general function to grab the data from the
    data portion of the binary file, organized according to the
    information in the headers.

    Arguments:
        fp {str or Path} -- Filepath
        headers {dict} -- All information parsed from the header
                          bytes.

    Raises:
        ValueError: f"{midas_type} either not yet supported or
                    not recognized.

    Returns:
        [Pandas DataFrame] -- Data stored in the MIDAS binary
                              file's data block, organized
                              according to info in the headers.
    """

    # NOTE: Get rid of dependence of the fix_head and just pull
    # the value from the binary file so that this method can
    # be used as a stand-alone.

    # Grab the type
    midas_type = headers["fix"]["midas_type"]

    if midas_type == 1000 or midas_type == 1001:

        df = parse_type_1000_data(fp=fp, headers=headers)

    elif midas_type == 2000:

        df = parse_type_2000_data(fp=fp, headers=headers)

    else:

        raise ValueError(
            [f"{midas_type} either not yet supported or ", "not recognized."]
        )

    return df


def parse_type_1000_data(fp, headers):
    """Defines the data structure of a MIDAS Type 1000 file format
    given the values in the header and parses the binary file such
    that the data can be stored in a Pandas DataFrame.

    Type 1000 files represent a series of homogeneous samples.
    IQ data captures ((I_0, Q_0), (I_1, Q_1), ...) is an
    example of data of this type. As such, each row corresponds
    to a sample.

    Arguments:
        fp {str or Path} -- Filepath to the MIDAS type 2000 binary
                            file.
        headers {NumPy ndarray} -- Structured array containing all
                                   information parsed from the
                                   MIDAS file's headers.

    Returns:
        [Pandas DataFrame] -- Data captured in the Data Block
                              section of the MIDAS type 1000
                              binary file.
    """

    # Construct the dtype for the data block
    d_size, d_type = data_format_code_to_np_designation(
        data_format=headers["fix"]["data_format"]
    )

    d_end = determine_np_endianness(
        byte_endianness=headers["fix"]["data_rep"].decode("latin-1")
    )

    if d_size == 1:
        homogenous_dt_obj = [("samples", f"{d_end}{d_type}")]
    elif d_size == 2:
        homogenous_dt_obj = [
            ("I", f"{d_end}{d_type}"),
            ("Q", f"{d_end}{d_type}"),
        ]
    else:
        homogenous_dt_obj = [("samples", (f"{d_end}{d_type}", d_size))]

    homogenous_dt = np.dtype(homogenous_dt_obj)

    # Find where the data starts and how many data elements to
    # grab
    n_bytes_per_data_ele = num_bytes_per_data_element(headers=headers)
    tot_bytes_of_data = headers["fix"]["data_size"]

    n_data_ele = int(np.floor(tot_bytes_of_data / n_bytes_per_data_ele))

    data_start_byte = int(headers["fix"]["data_start"])

    # Construct the "x-axis" range
    x_0 = headers["var"]["x_start"]
    dx = headers["var"]["x_delta"]
    x_units = units_code_to_str(code=headers["var"]["x_units"])

    x_vals = [x_0 + (pt * dx) for pt in range(n_data_ele)]

    # Pull data frames from the MIDAS Type 1000 file
    midas_1000_frames = np.fromfile(
        file=fp, dtype=homogenous_dt, count=n_data_ele, offset=data_start_byte
    )

    # Construct the Pandas DataFrame with data_arr and x_vals
    df = pd.DataFrame(
        midas_1000_frames, columns=midas_1000_frames.dtype.names, index=x_vals
    )
    df.index.rename(x_units, inplace=True)

    return df


def parse_type_2000_data(fp, headers):
    """Defines the data structure of a MIDAS Type 2000 file format
    given the values in the header and parses the binary file such
    that the data can be stored in a Pandas DataFrame.

    Type 2000 files represent a series of homogeneous records.
    Power in FFT bins (P_0, P_deltaf, P_2deltaf, ...) is an
    example of data of this type. As such, each row corresponds
    to a frame and each column represents a homogenous bin.

    Arguments:
        fp {str or Path} -- Filepath to the MIDAS type 2000 binary
                            file.
        headers {NumPy ndarray} -- Structured array containing all
                                   information parsed from the
                                   MIDAS file's headers.

    Returns:
        [Pandas DataFrame] -- Data captured in the Data Block
                              section of the MIDAS type 2000
                              binary file.
    """

    # Get number of data frames to look for and where to start looking
    data_ele_per_frame = headers["var"]["subsize"]
    n_bytes_per_data_ele = num_bytes_per_data_element(headers=headers)
    n_bytes_per_frame = n_bytes_per_data_ele * data_ele_per_frame

    tot_bytes_of_data = headers["fix"]["data_size"]

    num_frames = int(np.floor(tot_bytes_of_data / n_bytes_per_frame))

    data_start_byte = int(headers["fix"]["data_start"])

    # Check for a SUBREC_DESCRIP field in the extended header
    # and if it exists, grab its bytestring
    subrec_desc_exists = False

    for kw in range(len(headers["ext"])):
        if headers["ext"][kw]["tag"].decode("latin-1") == "SUBREC_DEF":
            subrec_desc_exists = True
            subrec_def_bstr = headers["ext"][kw]["value"]

    # If there is no SUBREC_DESCRIP in the ext header, we are dealing
    # with a true MIDAS type 2000 file and can parse it according to
    # the values in the var head

    if subrec_desc_exists is False:

        # Construct the "x-axis" range, which correspond to our
        # labels, according to the frame subsize
        x_0 = headers["var"]["x_start"]
        dx = headers["var"]["x_delta"]
        x_units = units_code_to_str(code=headers["var"]["x_units"])

        x_keys = [
            f"{(x_0 + (pt * dx))} {x_units}"
            for pt in range(data_ele_per_frame)
        ]

        # Define the NumPy dtype to hold one particular frame by finding
        # the NumPy designator for one data element
        d_size, d_type = data_format_code_to_np_designation(
            data_format=headers["fix"]["data_format"]
        )

        end = determine_np_endianness(
            byte_endianness=headers["fix"]["data_rep"].decode("latin-1")
        )

        if d_size != 1:
            frame_dt_obj = [
                (f"{x_k}", (f"{end}{d_type}", d_size)) for x_k in x_keys
            ]
        else:
            frame_dt_obj = [(f"{x_k}", f"{end}{d_type}") for x_k in x_keys]

        frame_dt = np.dtype(frame_dt_obj)

        # Construct the "y-axis" keys
        y_0 = headers["var"]["y_start"]
        dy = headers["var"]["y_delta"]
        y_units = units_code_to_str(code=headers["var"]["y_units"])

        y_keys = [(y_0 + (pt * dy)) for pt in range(num_frames)]

        # Parse the frames from the binary file
        midas_2000_frames = np.fromfile(
            file=fp, dtype=frame_dt, count=num_frames, offset=data_start_byte
        )

        # Create the Pandas DataFrame from these frames
        df = pd.DataFrame(
            midas_2000_frames,
            columns=midas_2000_frames.dtype.names,
            index=y_keys,
        )
        df.index.rename(y_units, inplace=True)

    # If there is a subrecord description in the extended header, it is
    # indicative of a MIDAS type 6000 file that has been converted into
    # a type 2000 and it must be parsed differently

    else:

        # Find the Endianness of the extended header
        h_end = determine_np_endianness(
            byte_endianness=headers["fix"]["head_rep"].decode("latin-1")
        )

        # Find the number of bytes in the bytestring that holds the
        # keywords in the SUBREC_DEF
        n_bytes_in_subrec_def = len(subrec_def_bstr)
        n_kw_in_subrec_def = int(n_bytes_in_subrec_def / 96)

        # Provide the NumPy dtype for a SUBREC_DEF keyword
        name = ("name", (f"{h_end}a", 24))
        min_val = ("min_val", (f"{h_end}a", 24))
        max_val = ("max_val", (f"{h_end}a", 24))
        offset = ("offset", (f"{h_end}a", 8))
        num_elts = ("num_elts", (f"{h_end}a", 4))
        units = ("units", (f"{h_end}a", 4))
        data_format = ("data_format", (f"{h_end}a", 2))
        u_prefix = ("u_prefix", (f"{h_end}a", 3))
        padding = ("padding", ("a", 3))

        subrec_def_kw_dtype_obj = [
            name,
            min_val,
            max_val,
            offset,
            num_elts,
            units,
            data_format,
            u_prefix,
            padding,
        ]

        subrec_def_kw_dtype = np.dtype(subrec_def_kw_dtype_obj)

        # Parse the bytestrings into NumPy Structured ndarrays
        subrec_def_kws = np.frombuffer(
            buffer=subrec_def_bstr,
            dtype=subrec_def_kw_dtype,
            count=n_kw_in_subrec_def,
        )

        # Decode and translate each keyword in SUBREC_DEF struct array
        # into a new dictionary
        subrec_def_kw_dict = decode_and_translate_subrec_def_keywords(
            subrec_def_kws=subrec_def_kws, headers=headers
        )

        # print(f"subrec_def_kw_dict: {subrec_def_kw_dict}")

        # Construct the NumPy dtype given the values in SUBREC_DEF dict
        frame_dt_obj = [
            (name, kw["data_format"])
            for name, kw in subrec_def_kw_dict.items()
        ]
        frame_dt = np.dtype(frame_dt_obj)

        # Parse the frames from the binary file
        midas_2000_frames = np.fromfile(
            file=fp, dtype=frame_dt, count=num_frames, offset=data_start_byte
        )

        # Create the Pandas DataFrame from these frames
        df = pd.DataFrame(
            midas_2000_frames, columns=midas_2000_frames.dtype.names
        )

        # print(f"DataFrame shape: {df.shape}")

        return df


def decode_and_translate_subrec_def_keywords(subrec_def_kws, headers):
    """Takes a Structured NumPy ndarray, each row representing a kw whose
    labeled dtypes contain byte strings that correspond to the keyword
    values in a MIDAS Type 6000 SUBREC_DEF (see Table 23 in MIDAS BLUE
    File Format documentation).

    Arguments:
        subrec_def_kws {NumPy ndarray} -- Structured array containing
                                          labeled dtypes that correspond
                                          to each subrecord keyword's
                                          byte field.

    Returns:
        [dict] -- Keywords whose respective subrecord fields have been
                  translated from byte strings to usable Python vars
    """
    # Grab Endianness for the data
    dat_end = determine_np_endianness(
        byte_endianness=headers["fix"]["data_rep"].decode("latin-1")
    )

    # Create a dict for the SUBREC_DEF keywords
    subrec_def_kw_dict = {}

    # Decode all the values describing each of the keywords into usable
    # Python formats
    for kw in subrec_def_kws:
        keyword_dict = {}

        name = kw["name"].decode("latin-1").strip()

        keyword_dict["min_val"] = float(kw["min_val"].decode("latin-1"))
        keyword_dict["max_val"] = float(kw["max_val"].decode("latin-1"))

        keyword_dict["offset"] = int(kw["offset"].decode("latin-1"))

        keyword_dict["num_elts"] = int(kw["num_elts"].decode("latin-1"))

        kw_units = units_code_to_str(int(kw["units"].decode("latin-1")))
        keyword_dict["units"] = kw_units
        keyword_dict["u_prefix"] = None

        kw_dat_format_code = kw["data_format"]
        kw_dat_size, kw_dat_type = data_format_code_to_np_designation(
            data_format=kw_dat_format_code
        )
        if kw_dat_size != 1:
            kw_dtype = (f"{dat_end}{kw_dat_type}", kw_dat_size)
        else:
            kw_dtype = f"{dat_end}{kw_dat_type}"
        keyword_dict["data_format"] = kw_dtype

        subrec_def_kw_dict[f"{name} ({kw_units})"] = keyword_dict

    return subrec_def_kw_dict


def num_bytes_per_data_element(headers):
    """Finds the number of bytes per data element (Scalar, Complex,
    Vector, etc.).

    Arguments:
        headers {NumPy ndarray} -- Structured array containing
                                   labled values of the MIDAS
                                   fixed header.

    Returns:
        [type] -- [description]
    """
    # Grab the NumPy designation for each data_format char
    samps_per_data_ele, _ = data_format_code_to_np_designation(
        data_format=headers["fix"]["data_format"]
    )

    # Given the data type, determine the number of bytes per
    # dtype and multiply it by how many samples there are
    # per data element
    n_bytes_per_samp = num_bytes_given_dtype(
        type_designator=headers["fix"]["data_format"].decode("latin-1")[1]
    )

    n_bytes_per_data_ele = samps_per_data_ele * n_bytes_per_samp

    return n_bytes_per_data_ele


def data_format_code_to_np_designation(data_format):
    """Translates the byte string of a MIDAS BLUE header that indicates
    the data type of the data stored into a format usable by the
    NumPy dtype class.

    Arguments:
        data_format {bstr} -- Byte string containing the parsed value
                              indicating the format of the data in a
                              MIDAS BLUE file.

    Raises:
        ValueError: data_format code length is {len(data_format)}.
                    It should be a max of two characters.

    Returns:
        [tuple] -- (dat_size, np_type) tuple containing an int
                   and a str respectively indicating the size
                   and format used by NumPy dtype to format its
                   binary parsing tools.
    """
    # Decode the bytestring the data_format was parsed as
    data_format_str = data_format.decode("latin-1")

    # If size and type is included, translate both
    if len(data_format) == 2:

        size_designator = data_format_str[0]
        np_dat_size = data_size_designator_to_np_equiv(
            size_designator=size_designator
        )

        type_designator = data_format_str[1]
        np_type = data_type_designator_to_np_equiv(
            type_designator=type_designator
        )

        return np_dat_size, np_type

    elif len(data_format) == 1:

        type_designator = data_format_str[0]
        np_type = data_type_designator_to_np_equiv(
            type_designator=type_designator
        )

        return None, np_type

    else:
        raise ValueError(
            [
                f"data_format code length is {len(data_format)}. ",
                "It should be a max of two characters.",
            ]
        )


def data_size_designator_to_np_equiv(size_designator):
    """Translates the character used in MIDAS BLUE files that
    indicate the size of a data field to its integer valued
    equivalent.

    Arguments:
        size_designator {str} -- MIDAS BLUE data size character.

    Returns:
        [int] -- Number of data points per sample capture.
    """
    size_dict = {
        "S": 1,
        "C": 2,
        "V": 3,
        "Q": 4,
        "M": 9,
        "T": 16,
        "X": 10,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
    }

    return size_dict[size_designator]


def data_type_designator_to_np_equiv(type_designator):
    """Translates the character used in MIDAS BLUE files that
    indicate the type of a data field to its NumPy dtype class
    indicatior equivalent.

    Arguments:
        type_designator {str} -- Character  in a MIDAS BLUE file
                                 that designates a type of data
                                 (int, float, char, etc.)

    Returns:
        [str] -- NumPy dtype representation
    """
    type_to_np_symb_dict = {
        "B": "i1",
        "O": "u",
        "I": "i2",
        "L": "i4",
        "X": "i8",
        "F": "f4",
        "D": "f8",
        "A": "a",
    }

    # TODO: Still need to handle - P, KW, NH

    return type_to_np_symb_dict[type_designator]


def num_bytes_given_dtype(type_designator):
    """Finds the number of bytes of the data type given the
    corresponding key value in the MIDAS BLUE fixed header.

    Arguments:
        type_designator {str} -- Character  in a MIDAS BLUE file
                                 that designates a type of data
                                 (int, float, char, etc.)

    Returns:
        [str] -- NumPy dtype representation
    """
    type_to_size_dict = {
        "B": 1,
        "O": 1,
        "I": 2,
        "L": 4,
        "X": 8,
        "F": 4,
        "D": 8,
        "A": 1,
    }

    # TODO: Still need to handle - P, KW, NH

    return type_to_size_dict[type_designator]


def units_code_to_str(code):
    """Translates MIDAS BLUE integer value code indicating
    units to a string representation.

    Arguments:
        code {int} -- MIDAS BLUE integer value units code.

    Returns:
        [str] -- Units
    """
    units_dict = {
        0: "N/A",
        1: "s",
        2: "s",
        3: "Hz",
        4: "tcode",
        5: "m",
        6: "m s^-1",
        7: "m s^-2",
        8: "m s^-3",
        9: "Hz",
        10: "Hz s^-1",
        11: "J",
        12: "W",
        13: "g",
        14: "dm^3",
        15: "W sr^-1",
        16: "W rad^-1",
        17: "W m^-2",
        18: "W m^-1",
        19: "W MHz^-1",
        30: "Uknown",
        31: "None",
        32: "Counts",
        33: "rad",
        34: "deg",
        35: "dB",
        36: "dBm",
        37: "dBW",
        38: "sr",
        40: "ft",
        41: "nmi",
        42: "ft s^-1",
        43: "nmi s^-1",
        44: "kt",
        45: "ft s^-2",
        46: "nm s^-2",
        47: "kt s^-1",
        48: "g",
        49: "g s^-1",
        50: "rps",
        51: "rpm",
        52: "rad s^-1",
        53: "deg s^-1",
        54: "rad s^-2",
        55: "deg s^-2",
        56: "%",
        57: "psi",
        58: "Unknown",
        59: "Unknown",
        60: "Latitude (deg)",
        61: "Longitude (deg)",
        62: "Altitude (ft)",
        63: "Altitude (m)",
    }
    return units_dict[code]


# TODO: The example command...
#
# pdwanalyzer stats-report
#  --single_file
#       2020-01-16_08-20-37_333275697hz_chan1_pdw.tmp
#  --gen_pdf
#       C:\Users\csmith657\Desktop\pdw-analysis\bin\archer-pdw-midas2000-examples
#
# ....that file is a Midas 2000 format. You need to redo the PDW capture
# and see what the french went wrong. Or write up Midas 2000 as well.

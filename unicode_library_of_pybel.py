#%%
import argparse
import random
import string
import sys
import typing

import codestrings

TEST_MODE: bool = False
charset: str = codestrings.CLASSIC
CUSTOM_ADDRESS: typing.Optional[str] = None
LENGTH_OF_PAGE: int = 3239
LENGTH_OF_TITLE: int = 25
loc_mult: int = pow(len(charset)+1, LENGTH_OF_PAGE)
title_mult: int = pow(len(charset)+1, LENGTH_OF_TITLE)
_B: int = 36
MINUS_SIGN: str = '\x7f' # We want to support charsets that contain "-" so we use DEL as a minus sign in the following functions

# This happens if someone sets charset = ' ' (Other characters don't work because exact match uses spaces for padding)
# This means that every page of every book is the same. Why did I feel the need to handle this? I don't know
def string_to_number_1(i_string: str) -> int:
    if i_string and i_string[0] == MINUS_SIGN:
        sign = -1
        i_string = i_string[1:]
    else:
        sign = 1
    first_term = len(i_string) # sum(pow(len(charset),i) for i in range(len(iString)))
    return sign * first_term # second term is always zero

# string_to_number = to_text^-1
def string_to_number_n(i_string: str) -> int:
    if i_string and i_string[0] == MINUS_SIGN:
        sign = -1
        i_string = i_string[1:]
    else:
        sign = 1
    # first_term == sum(pow(len(charset),i) for i in range(len(iString)))
    first_term = (len(charset)**(len(i_string)-1+1) - 1) // (len(charset)-1)
    return sign*(first_term + sum(pow(len(charset),i) * charset.index(x)
                                   for i, x in enumerate(i_string)))

def to_text(x: int) -> str:
    sign = signum(x)
    x *= sign
    digs = charset
    if TEST_MODE:
        assert MINUS_SIGN not in digs
    length = 0
    first_term = 0 # First term of the sum string_to_number returns
    d = pow(len(digs),length)
    while first_term+d <= x:
        first_term += d
        length += 1
        d = pow(len(digs),length)
    x -= first_term
    digits = []
    base = len(digs)
    while x:
        q, r = divmod(x, base)
        digits.append(digs[r])
        x = q
    digits += digs[0] * (length - len(digits))
    if sign < 0:
        digits = [MINUS_SIGN] + digits
    return ''.join(digits)

string_to_number = string_to_number_n

# copysign might throw OverflowError
def signum(x, /) -> int:
    try:
        return abs(x) // x
    except ZeroDivisionError:
        return 0

def text_prep(text: str) -> str:
    digs = set(charset)
    prepared = ''
    for letter in text:
        if letter in digs:
            prepared += letter
        elif letter.lower() in digs:
            prepared += letter.lower()
        elif letter == '\n':
            prepared += ' '
    return prepared

def filed(input_args, text: str) -> None:
    if input_args.file:
        with open(input_args.file, 'w', encoding="utf-8") as file:
            file.writelines(text)
        print('\nFile '+ input_args.file + ' was writen')


def test() -> None:
    global TEST_MODE
    TEST_MODE = True
    assert string_to_number('') == 0, string_to_number('')
    # assert string_to_number('ba') == 29, string_to_number('ba')
    page_length = len(get_page('asaskjkfsdf:2:2:2:33'))
    assert page_length == LENGTH_OF_PAGE, page_length
    assert 'hello kitty' == to_text(int(int2base(string_to_number('hello kitty'), _B), _B))
    assert int2base(4, 36) == '4', int2base(4, 36)
    assert int2base(10, 36) == 'A', int2base(10, 36)
    assert int2base(10, 36) == _integer_to_base(10, string.digits + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    test_string = '.................................................'
    assert test_string in get_page(search(test_string))
    print ('Tests completed')


def main() -> None:
    class CapitalisedHelpFormatter(argparse.RawTextHelpFormatter):
        """
        Cosmetics. Used to override 'usage: ' string to 'Usage: '
        """

        def add_usage(self, usage, actions, groups, prefix=None):

            if prefix is None:
                prefix = 'Usage: '

            return super(CapitalisedHelpFormatter, self).add_usage(usage, actions, groups, prefix)

    arg_parser = argparse.ArgumentParser(formatter_class=CapitalisedHelpFormatter,
                                         add_help=False)

    arg_parser.add_argument("-h", "--help", action="help",
                            default=argparse.SUPPRESS)
    arg_parser.add_argument("-f","--file",
                            dest="file",help="Dump result into the file")
    arg_parser.add_argument("-cm", "--charset-mode",
                             dest="charset_mode", help="Chooses what the charset will be")

    arg_address = arg_parser.add_mutually_exclusive_group(required=False)
    arg_address.add_argument("-ac", "--address-charset",
                             dest="address_charset", help = "Chooses what the address charset will be.")
    arg_address.add_argument("-ab", "--address-base",
                             dest = "address_base", help = "Chooses the base of the address. Base 36 is used by default and is also the highest supported")

    arg_input = arg_parser.add_mutually_exclusive_group(required=True)

    arg_input.add_argument("-c", "--checkout",
                           dest="checkout", help="Checks out a page of a book. Also displays the page's title.")
    arg_input.add_argument("-s","--search",
                           dest="search", help="""Does 3 searches for the text you input:
>Page contains: Finds a page which contains the text.
>Page only contains: Finds a page which only contains that text and nothing else.
>Title match: Finds a title which is exactly this string. For a title match, it will only match the first 25 characters. Addresses returned for title matches will need to have a page number added to the tail end, since they lack this.
Mind the quotemarks.""")
    arg_input.add_argument("-t","--test",
                           dest="test",action="store_true")
    arg_input.add_argument("-sf","--fsearch",
                           dest="fsearch", help="Does the same as search, but with text in the file.")
    arg_input.add_argument("-cf","--fcheckout",
                           dest="fcheckout", help="Does the same as checkout, but with address in the file. This truncates the last digit of the page number without a newline at EOF")

    input_args = arg_parser.parse_args()
    charset_modes = {'binary': codestrings.BINARY,
                     'morse': codestrings.MORSE,
                     'borges': codestrings.BORGES,
                     'classic': codestrings.CLASSIC,
                     'full': codestrings.FULL,
                     'unicode': codestrings.UNICODE_REGULAR}
    global charset
    global CUSTOM_ADDRESS
    CUSTOM_ADDRESS = input_args.address_charset
    if input_args.address_charset and input_args.address_charset in charset_modes:
        if input_args.address_charset == 'unicode':
            CUSTOM_ADDRESS = codestrings.UNICODE_ADDRESS
        else:
            CUSTOM_ADDRESS = charset_modes[input_args.address_charset]
            if '-' in CUSTOM_ADDRESS:
                raise NotImplementedError("Please choose a charset that does not contain '-'.") # See _base_to integer
    else:
        CUSTOM_ADDRESS = None
    global _B
    if CUSTOM_ADDRESS is None:
        sys.set_int_max_str_digits(20000) # Could probably be lower. It could also be avoided altogether if we didn't use the builtin int to convert from base _B
        if input_args.address_base:
            _B = int(input_args.address_base)
            if _B > 36:
                raise NotImplementedError # the digs variable in int2base can be extended to allow higher bases
        else:
            _B = 36
    if input_args.charset_mode and input_args.charset_mode in charset_modes:
        charset = charset_modes[input_args.charset_mode]
    else:
        charset = codestrings.CLASSIC # Fall back to default
    global string_to_number
    if len(charset) == 1:
        string_to_number = string_to_number_1
    else:
        string_to_number = string_to_number_n
    global loc_mult,title_mult
    loc_mult = pow(len(charset)+1, LENGTH_OF_PAGE)
    title_mult = pow(len(charset)+1, LENGTH_OF_TITLE)
    if input_args.checkout:
        key_str = input_args.checkout
        text  ='\nTitle: '+get_title(key_str) + '\n'+get_page(key_str)+'\n'
        print(text)
        filed(input_args, text)
    elif input_args.search:
        search_str = text_prep(input_args.search)
        key_str = search(text_prep(search_str))
        text1 = '\nPage which includes this text:\n' + get_page(key_str)+'\n\n@ address '+key_str+'\n'
        only_key_str = search(search_str.ljust(LENGTH_OF_PAGE))
        text2 = '\nPage which contains only this text:\n'+ get_page(only_key_str)+'\n\n@ address '+only_key_str+'\n'
        text3 = '\nTitle which contains this text:\n@ address '+ search_title(search_str)
        text = text1 + text2 + text3
        print(text)
        filed(input_args, text)
    elif input_args.test:
        test()
    elif input_args.fsearch:
        file = input_args.fsearch
        with open(file, 'r',encoding = "utf-8") as f:
            lines = ''.join([line for line in f.readlines() if line != '\n'])
        search_str = text_prep(lines)
        key_str = search(search_str)
        text1 = '\nPage which includes this text:\n' + get_page(key_str) + '\n\n@ address '+ key_str + '\n'
        only_key_str = search(search_str.ljust(LENGTH_OF_PAGE))
        text2 = '\nPage which contains only this text:\n' + get_page(only_key_str) + '\n\n@ address ' + only_key_str + '\n'
        text3 = '\nTitle which contains this text:\n@ address ' + search_title(search_str) + '\n'
        text = text1 + text2 + text3
        print(text)
        filed(input_args, text)
    elif input_args.fcheckout:
        file = input_args.fcheckout
        with open(file, 'r',encoding="utf-8") as f:
            key_str = ''.join([line for line in f.readlines() if line != '\n'])[:-1]
        text  ='\nTitle: ' + get_title(key_str) + '\n'+get_page(key_str) + '\n'
        print(text)
        print(key_str)
        filed(input_args, text)

def search(search_str: str) -> str:
    wall = str(int(random.random()*4))
    shelf = str(int(random.random()*5))
    volume = str(int(random.random()*32)).zfill(2)
    page = str(int(random.random()*410)).zfill(3)
    #the string made up of all of the location numbers
    loc_str = page + volume + shelf + wall
    loc_int = int(loc_str) #make integer
    digs = charset
    hex_addr = ''
    depth = int(random.random()*(LENGTH_OF_PAGE-len(search_str)))
    #random padding that goes before the text
    front_padding = ''
    for _ in range(depth):
        front_padding += digs[int(random.random()*len(digs))]
    #making random padding that goes after the text
    back_padding = ''
    for _ in range(LENGTH_OF_PAGE-(depth+len(search_str))):
        back_padding += digs[int(random.random()*len(digs))]
    search_str = front_padding + search_str + back_padding
    hex_addr = integer_to_base(string_to_number(search_str)+(loc_int*loc_mult)) #change to base b (b depends on if -u is passed) and add loc_int, then make string
    key_str = hex_addr + ':' + wall + ':' + shelf + ':' + volume + ':' + page
    if TEST_MODE:
        page_text = get_page(key_str)
        assert page_text == search_str, '\npage text:\n'+page_text+'\nstrings:\n'+search_str
    return key_str

def get_title(address: str) -> str:
    address_array = address.split(':')
    hex_addr = address_array[0]
    wall = address_array[1]
    shelf = address_array[2]
    volume = address_array[3].zfill(2)
    loc_int = int(volume+shelf+wall)
    key = base_to_integer(hex_addr)
    key -= loc_int * title_mult
    str_b = integer_to_base(key)
    result = to_text(base_to_integer(str_b))
    if len(result) < LENGTH_OF_TITLE:
        #adding pseudorandom chars
        random.seed(result)
        digs = charset
        while len(result) < LENGTH_OF_TITLE:
            result += digs[int(random.random()*len(digs))]
    elif len(result) > LENGTH_OF_TITLE:
        result = result[-LENGTH_OF_TITLE:]
    return result

def search_title(search_str: str) -> str:
    wall = str(int(random.random() * 4))
    shelf = str(int(random.random() * 5))
    volume = str(int(random.random() * 32)).zfill(2)
    #the string made up of all of the location numbers
    loc_str = volume + shelf + wall
    loc_int = int(loc_str) #make integer
    hex_addr = ''
    search_str = search_str[:LENGTH_OF_TITLE].ljust(LENGTH_OF_TITLE)
    hex_addr = integer_to_base(string_to_number(search_str) + (loc_int * title_mult))
    key_str = hex_addr + ':' + wall + ':' + shelf + ':' + volume
    if TEST_MODE:
        assert search_str == get_title(key_str)
    return key_str

def get_page(address: str) -> str:
    hex_addr, wall, shelf, volume, page = address.split(':')
    volume = volume.zfill(2)
    page = page.zfill(3)
    loc_int = int(page+volume+shelf+wall)
    key = base_to_integer(hex_addr)
    key -= loc_int * loc_mult
    str_b = integer_to_base(key)
    result = to_text(base_to_integer(str_b))
    if len(result) < LENGTH_OF_PAGE:
        #adding pseudorandom chars
        random.seed(result)
        digs = charset
        while len(result) < LENGTH_OF_PAGE:
            result += digs[int(random.random() * len(digs))]
    elif len(result) > LENGTH_OF_PAGE:
        result = result[-LENGTH_OF_PAGE:]
    return result

def int2base(number: int, base: int) -> str:
    digs = string.digits + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if number < 0:
        sign = -1
    elif number == 0:
        return digs[0]
    else: sign = 1
    number *= sign
    digits: list[str] = []
    while number:
        q, r = divmod(number, base)
        digits.append(digs[r])
        number = q
    if sign < 0:
        digits.append('-')
    digits.reverse()
    return ''.join(digits)

def _integer_to_base(number: int, base_string: str) -> str:
    """
    Converts base10 integer to baseX integer (where X is the length of base_string, say X for '0123' is 4),
    for example: 2645608968347327576478451524936 (Which is 'Hello, world!') to 21646C726F77202C6F6C6C6548 (base16),
    does account for negative numbers
    """
    if number < 0:
        sign = -1
    elif number == 0:
        return base_string[0]
    else: sign = 1
    number *= sign
    digits: list[str] = []
    base_length = len(base_string)

    while number:
        q, r = divmod(number, base_length)
        digits.append(base_string[r])
        number = q
    if sign < 0:
        digits.append('-')
    return ''.join(list(reversed(digits)))

def integer_to_base(number: int) -> str:
    if CUSTOM_ADDRESS:
        return _integer_to_base(number, CUSTOM_ADDRESS)
    else:
        return int2base(number, _B)

def _base_to_integer(base_number: str, base_string: str) -> int:
    """
    Converts baseX integer to base10 integer (where X is the length of base_string, say X for '0123' is 4),
    for example: 21646C726F77202C6F6C6C6548 (base16) to 2645608968347327576478451524936 (Which is 'Hello, world!'),
    does account for negative numbers
    """
    number = 0
    if base_number[0] == '-':
        sign =- 1
        base_number = base_number[1:]
    else:
        sign = 1

    for digit in str(base_number):
        number = number * len(base_string) + base_string.index(digit)

    return number * sign

def base_to_integer(base_number: str) -> int:
    if CUSTOM_ADDRESS:
        return _base_to_integer(base_number, CUSTOM_ADDRESS)
    else:
        return int(base_number, _B)

if __name__ == "__main__":
    main()

# %%

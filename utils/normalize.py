#!/usr/bin/env python2

import rivendell

import argparse
import datetime
import re
import sys
import os

argparser = argparse.ArgumentParser(
    description='''
        A cart normalizing utility for Rivendell, based on EBU R128 recommendations.
        ''',)
argparser.add_argument('-d', '--dry-run', action='store_true', help="do not modify files or database")
argparser.add_argument('-H', '--hard', action='store_true', help='''modify actual cuts instead of play_gain value''')
_log = argparser.add_mutually_exclusive_group()
_log.add_argument('--log', action='store', default="normalize.log", help='''specify a name for the log file.
    by default, logs to file "normalize.log"''')
_log.add_argument('--no-log', action='store_const', dest="log",
    const=None, default='normalize.log', help='disables logging')
#argparser.add_argument('--album', action='store_true')
argparser.add_argument('-t', '--target-loudness', default=-18, type=float, help='''desired loudness level''')
argparser.add_argument('-D', '--delta', default=30, type=int, help='''specifies a minimum level difference
                       before applying normalization. This is expressed in hundredths of dB (100 = 1dB)
                       (default 30)''')
argparser.add_argument('-M', '--maximum', default=5, type=float, help='''maximum gain to apply to original cut (default 5dB)''')
argparser.add_argument('cartrange', nargs='+', 
    help='''a space separated list of carts. Cart ranges in the format 000000-999999
        are also supported''')


args = argparser.parse_args()
if args.log:
    log_file = open(args.log, 'a')

def log(message):
    if log_file:
        now = datetime.datetime.now()
        now_str = now.strftime('%F %T')
        log_file.write("{}: {}\n".format(now_str, message))
        log_file.flush()
    return message

def normalize_cut(cut):
    try:
        cut_gain = cut.get_gain()
        cut_loudness = float(cut.get_loudness())
    
    except rivendell.exc.CutNotOnDisk as e:
        log("could not get cut {} (not on disk)".format(cut.cut_name))

    else:
        print "Cut({}): {} LUFS".format(cut.cut_name, cut_loudness)
        if not args.dry_run:
            target_gain = int( (args.target_loudness - cut_loudness)*100 )
            delta = abs(cut_gain - target_gain)

            if delta > args.maximum:
                log("Exceeding maximum ({} dB), will not modify".format(target_gain))  
            elif delta <= args.delta:
                print log("Same gain ({} dB). Not modified".format(target_gain/100.0))
            else:
                if not args.hard:
                    cut.set_gain( target_gain )
                    print "Cut gain was {} dB. Now {} dB".format(cut_gain/100.0, target_gain/100.0)
                    log("Modified play_gain: was {}, now {}".format(cut_gain, target_gain))
                else:
                    subprocess.

def main():
    print args

    log("Starting normalize session: {}\n" + 
        "Invoked with parameters \"{}\" " +
        "by user {}({})".format(args.cartrange, " ".join(sys.argv), os.getlogin(), os.getuid()) )

    try:
        host = rivendell.Host()
    except Exception as e:
        log("Could not connect to host. Error was {}".format(e))
        raise

    carts_to_do = args.cartrange
    cart_range_pattern = re.compile(r'^(\d{1,6})(?:-(\d{1,6}))?$')  # match pattern like "123456-654321"

    
    for number in carts_to_do:
        cart_range = cart_range_pattern.match(number).groups()
        cart_range_len = len(filter(None, cart_range))

        if cart_range[1] is not None:
            log("range: {}-{}".format(cart_range[0], cart_range[1]))
            cartrange = rivendell.CartRange(host._db, cart_range[0], cart_range[1])           
            log("got carts {}".format(cartrange.carts))
            
            # fetch all "cut" objects
            [cart.get_cuts() for cart in cartrange.carts]

            for cart in cartrange.carts:
                for cut in cart.cuts:
                    normalize_cut(cut)
                    
        elif cart_range[0] is not None and cart_range[1] is None:
            log("single cart: {}".format(cart_range[0])) 
            try:
                cart = host.get_cart(int(cart_range[0]))
            except rivendell.exc.CartNotInDatabase as e:
                print >>sys.stderr, log("Cart {} does not exist.".format(number))
            else:
                for cut in cart.cuts:
                    log("About to normalize cut({})".format(cut.cut_name))
                    normalize_cut(cut)

        else:
            raise ValueError('Invalid cart range specified! {}'.format(number))


        
    print "Done."

if __name__ == '__main__':
    try:
        main()
    finally:
        log("End of session\n" + 75*"*")


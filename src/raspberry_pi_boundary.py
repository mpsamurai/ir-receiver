import time
import logging
import pigpio

GPIO = 17
GLITCH = 100
GAP_S = 100 / 1000.0
PRE_US = 200 * 1000
POST_MS = 50
POST_US = POST_MS * 1000
FREQ = 38.0
SHORT = 10
TOLERANCE = 15
TOLER_MIN =  (100 - TOLERANCE) / 100.0
TOLER_MAX =  (100 + TOLERANCE) / 100.0

last_tick = 0
in_code = False
code = []
fetching_code = False
cancelled = False
logger = logging.getLogger(__name__)
sh = logging.StreamHandler()
logger.addHandler(sh)


class RespberryPiBoundary:
    
    def tidy_mark_space(self, records, base):

       ms = {}

       # Find all the unique marks (base=0) or spaces (base=1)
       # and count the number of times they appear,

       for rec in records:
          rl = len(records[rec])
          for i in range(base, rl, 2):
             if records[rec][i] in ms:
                ms[records[rec][i]] += 1
             else:
                ms[records[rec][i]] = 1

       v = None

       for plen in sorted(ms):

          # Now go through in order, shortest first, and collapse
          # pulses which are the same within a tolerance to the
          # same value.  The value is the weighted average of the
          # occurences.
          #
          # E.g. 500x20 550x30 600x30  1000x10 1100x10  1700x5 1750x5
          #
          # becomes 556(x80) 1050(x20) 1725(x10)
          #       
          if v == None:
             e = [plen]
             v = plen
             tot = plen * ms[plen]
             similar = ms[plen]

          elif plen < (v*TOLER_MAX):
             e.append(plen)
             tot += (plen * ms[plen])
             similar += ms[plen]

          else:
             v = int(round(tot/float(similar)))
             # set all previous to v
             for i in e:
                ms[i] = v
             e = [plen]
             v = plen
             tot = plen * ms[plen]
             similar = ms[plen]

       v = int(round(tot/float(similar)))
       # set all previous to v
       for i in e:
          ms[i] = v

       for rec in records:
          rl = len(records[rec])
          for i in range(base, rl, 2):
             records[rec][i] = ms[records[rec][i]]

    def tidy(self, records):

       self.tidy_mark_space(records, 0) # Marks.

       self.tidy_mark_space(records, 1) # Spaces.
    
    def normalise(self, c):
       """
       Typically a code will be made up of two or three distinct
       marks (carrier) and spaces (no carrier) of different lengths.

       Because of transmission and reception errors those pulses
       which should all be x micros long will have a variance around x.

       This function identifies the distinct pulses and takes the
       average of the lengths making up each distinct pulse.  Marks
       and spaces are processed separately.

       This makes the eventual generation of waves much more efficient.

       Input

         M    S   M   S   M   S   M    S   M    S   M
       9000 4500 600 540 620 560 590 1660 620 1690 615

       Distinct marks

       9000                average 9000
       600 620 590 620 615 average  609

       Distinct spaces

       4500                average 4500
       540 560             average  550
       1660 1690           average 1675

       Output

         M    S   M   S   M   S   M    S   M    S   M
       9000 4500 609 550 609 550 609 1675 609 1675 609
       """

       entries = len(c)
       p = [0]*entries # Set all entries not processed.
       for i in range(entries):
          if not p[i]: # Not processed?
             v = c[i]
             tot = v
             similar = 1.0

             # Find all pulses with similar lengths to the start pulse.
             for j in range(i+2, entries, 2):
                if not p[j]: # Unprocessed.
                   if (c[j]*TOLER_MIN) < v < (c[j]*TOLER_MAX): # Similar.
                      tot = tot + c[j]
                      similar += 1.0

             # Calculate the average pulse length.
             newv = round(tot / similar, 2)
             c[i] = newv

             # Set all similar pulses to the average value.
             for j in range(i+2, entries, 2):
                if not p[j]: # Unprocessed.
                   if (c[j]*TOLER_MIN) < v < (c[j]*TOLER_MAX): # Similar.
                      c[j] = newv
                      p[j] = 1

    def end_of_code(self):
       global code, fetching_code

       if len(code) > SHORT:
          self.normalise(code)
          fetching_code = False
       else:
          code = []
          logger.error("Short code, probably a repeat, try again")
    
    def cbf(self, gpio, level, tick):

       global last_tick, in_code, code, fetching_code

       if level != pigpio.TIMEOUT:
          edge = pigpio.tickDiff(last_tick, tick)
          last_tick = tick

          if fetching_code:

             if (edge > PRE_US) and (not in_code): # Start of a code.
                in_code = True
                self.pi.set_watchdog(GPIO, POST_MS) # Start watchdog.

             elif (edge > POST_US) and in_code: # End of a code.
                in_code = False
                self.pi.set_watchdog(GPIO, 0) # Cancel watchdog.
                self.end_of_code()

             elif in_code:
                code.append(edge)

       else:
          self.pi.set_watchdog(GPIO, 0) # Cancel watchdog.
          if in_code:
             in_code = False
             self.end_of_code()

    
    def start_capturing_remote_signal(self, callback):
        logger.debug('Start capturing remote signal')
        global code, fetching_code, cancelled
        
        self.pi = pigpio.pi() # Connect to Pi.

        if not self.pi.connected:
           logger.error('Failed to connect to raspberry pi')

        self.pi.set_mode(GPIO, pigpio.INPUT) # IR RX connected to this GPIO.
        self.pi.set_glitch_filter(GPIO, GLITCH) # Ignore glitches.
        cb = self.pi.callback(GPIO, pigpio.EITHER_EDGE, self.cbf)
        
        logger.debug('Capturing remote signal...')
        code = []
        fetching_code = True
        cancelled = False
        while fetching_code and not cancelled:
           time.sleep(0.1)
        if cancelled:
           logger.debug('Capturing remote signal...cancelled')
        else:
           logger.debug('Capturing remote signal...Done')
        time.sleep(0.5)
        
        self.pi.set_glitch_filter(GPIO, 0) # Cancel glitch filter.
        self.pi.set_watchdog(GPIO, 0) # Cancel watchdog.
        record = {'0': code}
        if not cancelled:
            self.tidy(record)
        callback(record, cancelled)
        
    def stop_capturing_remote_signal(self):
        global cancelled
        cancelled = True
#!/usr/bin/env python

container = "blabla"
new_command = ['kubectl', 'get', 'pod', '--no-headers']

new_command.insert(4, '--output')
new_command.insert(5, 'custom-columns=ADDRESS:.status.podIP')
new_command.extend(['-l', 'original-name=%s' % container])

print ' '.join(new_command)

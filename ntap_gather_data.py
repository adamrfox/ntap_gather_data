#!/usr/bin/python
from __future__ import print_function

import sys
sys.path.append('./xlsxwriter')
sys.path.append('./NetApp')
import xlsxwriter
from NaServer import *
import getopt
import getpass
from codecs import decode

class NetAppVol:
    def __init__(self, name, junction, space, inodes):
        self.name = name
        self.junction = junction
        self.space = space
        self.files = inodes

    def vol_data(self):
        return (self.name, self.junction, self.space, self.files)

def usage():
    print("Usage goes here")
    exit(0)
def get_creds_from_file (file):
    with open(file) as fp:
        data = fp.read()
    fp.close()
    if int(sys.version[0]) > 2:
        data = str.encode(data)
        data = decode(data, 'uu')
        data = decode(str(data), 'rot13')
        data = data.replace("o'", "")
        lines = data.split('\\a')
    else:
        data = decode(bytes(data), 'uu')
        data = decode(data, 'rot13')
        lines = data.splitlines()
    for x in lines:
        if x == "":
            continue
        xs = x.split(':')
        if xs[0] == "ntap":
            ntap_user = xs[1]
            ntap_password = xs[2]
    return (ntap_user, ntap_password)

def ntap_set_err_check(out):
    if(out and (out.results_errno() != 0)) :
        r = out.results_reason()
        print("Connection to filer failed" + r + "\n")
        sys.exit(2)

def ntap_invoke_err_check(out):
    if(out.results_status() == "failed"):
            print(out.results_reason() + "\n")
            sys.exit(2)

if __name__ == "__main__":
    user = ""
    password = ""
    DEBUG = False
    svm_list = []
    ntap_vols = {}
    ws = {}

    optlist, args = getopt.getopt(sys.argv[1:], 'hc:D', ['--help', '--creds=', '--debug'])
    for opt, a in optlist:
        if opt in ('-h', '--help'):
            usage()
        if opt in ('-c', '--creds'):
            if ':' in a:
                (user, password) = a.split(':')
            else:
                (user, password) = get_creds_from_file(a)
        if opt in ('-D', '--debug'):
            DEBUG = True

    (ntap, outfile) = args

    if user == "":
        if int(sys.version[0]) > 2:
            user = input("User: ")
        else:
            user = raw_input("User: ")
    if password == "":
        password = getpass.getpass("Password: ")

# Setup NTAP API Session

    netapp = NaServer(ntap, 1, 15)
    out = netapp.set_transport_type('HTTPS')
    ntap_set_err_check(out)
    out = netapp.set_style('LOGIN')
    ntap_set_err_check(out)
    out = netapp.set_admin_user(user, password)
    ntap_set_err_check(out)

    result = netapp.invoke('cluster-identity-get')
    ntap_invoke_err_check(result)
    cluster_info = result.child_get('attributes').child_get('cluster-identity-info')
    cluster_name = cluster_info.child_get_string('cluster-name')
    cluster_serial = cluster_info.child_get_string('cluster-serial-number')
    cluster_location = cluster_info.child_get_string('cluster-location')
    result = netapp.invoke('vserver-get-iter')
    ntap_invoke_err_check(result)
    vs_info = result.child_get('attributes-list').children_get()
    for vs in vs_info:
        vs_type = vs.child_get_string("vserver-type")
        if vs_type == "data":
            svm_list.append(vs.child_get_string('vserver-name'))
    result = netapp.invoke('volume-get-iter')
    vol_info = result.child_get('attributes-list').children_get()
    for vol in vol_info:
        info = vol.child_get('volume-id-attributes')
        name = info.child_get_string('name')
        svm = info.child_get_string('owning-vserver-name')
        if svm not in svm_list:
            continue
        junction = info.child_get_string('junction-path')
        if junction == "/":
            continue
        space = vol.child_get('volume-space-attributes')
        space_used = space.child_get_int('logical-used-by-afs')
        inodes = vol.child_get('volume-inode-attributes')
        inodes_used = inodes.child_get_int('files-used')
        try:
            ntap_vols[svm]
        except KeyError:
            ntap_vols[svm] = []
        ntap_vols[svm].append(NetAppVol(name, junction, space_used, inodes_used))
    wb = xlsxwriter.Workbook(outfile)
    bold = wb.add_format({'bold': True})
    heading = wb.add_format({'bold': True, 'underline': True})
    space_unit = wb.add_format({'num_format': '[<1000000000000]##0.00,,," GB";[<1000000000000000]##0.00,,,," TB";#,##0.00,,,,," PB"'})
    space_unit_total = wb.add_format({'num_format': '[<1000000000000]##0.00,,," GB";[<1000000000000000]##0.00,,,," TB";#,##0.00,,,,," PB"', 'bold': True})
    summary = wb.add_worksheet("Summary")
    summary.set_column(1, 1, 50)
    summary.set_column(2, 2, 20)
    summary.set_column(3, 3, 150)
    summary.write('B2', "Summary for: " + str(cluster_name), heading)
    summary.write('C2', "(SN: " + str(cluster_serial) + ")", heading)
    summary.write('D2', str(cluster_location), heading)
    sum_space = "=SUM("
    sum_files = "=SUM("
    first_sheet = True
    for svm in ntap_vols.keys():
        ws[svm] = wb.add_worksheet(svm)
        ws[svm].set_column(1, 2, 25)
        ws[svm].set_column(3, 4, 15)
        ws[svm].write('B2', 'Volume:', heading)
        ws[svm].write('C2', 'Mounted:', heading)
        ws[svm].write('D2', 'Size:', heading)
        ws[svm].write('E2', 'Files:', heading)
        row = 3
        for data in ntap_vols[svm]:
            (vol_name, vol_junction, vol_space, vol_files) = data.vol_data()
            ws[svm].write('B'+str(row), vol_name)
            ws[svm].write('C'+str(row), vol_junction)
            ws[svm].write('D'+str(row), vol_space, space_unit)
            ws[svm].write('E'+str(row), vol_files)
            row += 1
        row += 1
        ws[svm].write('B'+str(row), 'Totals:', bold)
        ws[svm].write('D'+str(row), '=SUM(D2:D' + str(row-2) +')', space_unit_total)
        ws[svm].write('E'+str(row), '=SUM(E2:E' + str(row-2) + ')', bold)
        if first_sheet:
            sum_space +=  svm + '!' + 'D' + str(row)
            sum_files +=  svm + '!' + 'E' + str(row)
            first_sheet = False
        else:
            sum_space += ',' + svm + '!' + 'D' + str(row)
            sum_files += ',' + svm + '!' + 'E' + str(row)
    sum_space += ")"
    sum_files += ")"
    summary.write('B4', "Total Space:")
    summary.write('B5', "Total Files:")
    summary.write('C4', sum_space, space_unit_total)
    summary.write ('C5', sum_files, bold)
    wb.close()



import os
import xml.etree.ElementTree as ET

def import_root_histogram(rootdir, filename, path, name):
    import uproot
    #import pdb; pdb.set_trace()
    #assert path == ''
    # strip leading slashes as uproot doesn't use "/" for top-level
    path = path.strip('/')
    f = uproot.open(os.path.join(rootdir, filename))
    try:
        return f[name].numpy[0]
    except KeyError:
        pass

    try:
        return f[os.path.join(path, name)].numpy[0]
    except KeyError:
        pass

    raise KeyError('Both {0:s} and {1:s} were tried and not found in {2:s}'.format(name, os.path.join(path, name), os.path.join(rootdir, filename)))

def process_sample(sample,rootdir,inputfile, histopath):
    if 'InputFile' in sample.attrib:
       inputfile = sample.attrib.get('InputFile')
    if 'HistoPath' in sample.attrib:
        histopath = sample.attrib.get('HistoPath')
    histoname = sample.attrib['HistoName']

    modifiers = []
    for modtag in sample.iter():
        if modtag.tag == 'OverallSys':
            modifiers.append({
                'name': modtag.attrib['Name'],
                'type': 'normsys',
                'data': {'lo': float(modtag.attrib['Low']), 'hi': float(modtag.attrib['High'])}
            })

        if modtag.tag == 'NormFactor':
            modifiers.append({
                'name': modtag.attrib['Name'],
                'type': 'normfactor',
                'data': None
            })

    return {
        'name': sample.attrib['Name'],
        'data': import_root_histogram(rootdir, inputfile, histopath, histoname).tolist(),
        'modifiers': modifiers
    }

def process_data(sample,rootdir,inputfile, histopath):
    if 'InputFile' in sample.attrib:
       inputfile = sample.attrib.get('InputFile')
    if 'HistoPath' in sample.attrib:
        histopath = sample.attrib.get('HistoPath')
    histoname = sample.attrib['HistoName']

    return import_root_histogram(rootdir, inputfile, histopath, histoname)

def process_channel(channelxml,rootdir):
    channel = channelxml.getroot()

    inputfile = channel.attrib.get('InputFile')
    histopath = channel.attrib.get('HistoPath')

    samples = channel.findall('Sample')


    data = channel.findall('Data')[0]

    return  channel.attrib['Name'], process_data(data, rootdir, inputfile, histopath), [process_sample(x, rootdir, inputfile, histopath) for x in samples]

def parse(configfile,rootdir):
    toplvl = ET.parse(configfile)
    inputs = [ET.parse(os.path.join(rootdir,x.text)) for x in toplvl.findall('Input')]
    channels = {
        k:{'data': d, 'samples': v} for k,d,v in [process_channel(inp,rootdir) for inp in inputs]
    }
    return {
        'toplvl':{
            'resultprefix':toplvl.getroot().attrib['OutputFilePrefix'],
            'measurements': {x.attrib['Name'] : {} for x in toplvl.findall('Measurement')}
        },
        'channels': [{'name': k, 'samples': v['samples']} for k,v in channels.items()],
        'data':     {k:v['data'] for k,v in channels.items()}
    }

###########################################################################################
# Copyright 2022 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


import pytest
from garmin_fit_sdk import Decoder, Stream


@pytest.mark.skip
@pytest.mark.parametrize(
    "filename",
    ['Corrupt_00000.fit', 'Corrupt_00001.fit', 'Corrupt_00002.fit', 'Corrupt_00003.fit', 'Corrupt_00004.fit', 'Corrupt_00005.fit', 'Corrupt_00006.fit',
    'Corrupt_00007.fit', 'Corrupt_00008.fit', 'Corrupt_00009.fit', 'Corrupt_00010.fit', 'Corrupt_00011.fit', 'Corrupt_00012.fit', 'Corrupt_00013.fit',
    'Corrupt_00014.fit', 'Corrupt_00015.fit', 'Corrupt_00016.fit', 'Corrupt_00017.fit', 'Corrupt_00018.fit', 'Corrupt_00019.fit', 'Corrupt_00020.fit',
    'Corrupt_00021.fit', 'Corrupt_00022.fit', 'Corrupt_00023.fit', 'Corrupt_00024.fit', 'TBD_00000.fit', 'TBD_00001.fit', 'TBD_00002.fit', 'TBD_00003.fit',
    'TBD_00004.fit', 'TBD_00005.fit', 'TBD_00006.fit', 'TBD_00007.fit', 'TBD_00008.fit', 'TBD_00009.fit', 'TBD_00010.fit', 'TBD_00011.fit', 'TBD_00012.fit',
    'TBD_00013.fit', 'TBD_00014.fit', 'TBD_00015.fit', 'TBD_00016.fit', 'TBD_00017.fit', 'TBD_00018.fit', 'TBD_00018.fit', 'TBD_00019.fit', 'TBD_00020.fit',
    'TBD_00021.fit', 'TBD_00022.fit', 'TBD_00023.fit', 'TBD_00024.fit', 'TBD_00025.fit', 'TBD_00026.fit', 'TBD_00027.fit', 'TBD_00028.fit', 'TBD_00029.fit',
    'TBD_00030.fit', 'TBD_00031.fit', 'TBD_00032.fit', 'TBD_00033.fit', 'TBD_00034.fit', 'TBD_00035.fit', 'TBD_00036.fit', 'TBD_00037.fit', 'TBD_00038.fit',
    'TBD_00039.fit', 'TBD_00040.fit', 'TBD_00041.fit', 'TBD_00042.fit', 'TBD_00043.fit', 'TBD_00044.fit', 'TBD_00045.fit', 'TBD_00046.fit', 'TBD_00047.fit',
    'TBD_00048.fit', 'TBD_00049.fit', 'TBD_00050.fit', 'TBD_00051.fit', 'TBD_00052.fit', 'TBD_00053.fit', 'TBD_00054.fit', 'TBD_00055.fit', 'TBD_00056.fit',
    'TBD_00057.fit', 'TBD_00058.fit', 'TBD_00059.fit', 'TBD_00060.fit', 'TBD_00061.fit', 'TBD_00062.fit', 'TBD_00063.fit', 'TBD_00064.fit', 'TBD_00065.fit',
    'TBD_00066.fit', 'TBD_00067.fit', 'TBD_00068.fit', 'TBD_00069.fit', 'TBD_00070.fit', 'TBD_00071.fit', 'TBD_00072.fit', 'TBD_00073.fit', 'TBD_00074.fit',
    'TBD_00075.fit', 'TBD_00076.fit', 'TBD_00077.fit', 'TBD_00078.fit', 'TBD_00079.fit', 'TBD_00080.fit', 'TBD_00081.fit', 'TBD_00082.fit', 'TBD_00083.fit',
    'TBD_00084.fit', 'TBD_00085.fit', 'TBD_00086.fit', 'TBD_00087.fit', 'TBD_00088.fit', 'TBD_00089.fit', 'TBD_00090.fit', 'TBD_00091.fit', 'TBD_00092.fit',
    'TBD_00093.fit', 'TBD_00094.fit', 'TBD_00095.fit', 'TBD_00096.fit', 'TBD_00097.fit', 'TBD_00098.fit', 'TBD_00099.fit', 'TBD_00100.fit', 'TBD_00101.fit',
    'TBD_00102.fit', 'TBD_00103.fit', 'TBD_00104.fit', 'TBD_00105.fit', 'TBD_00106.fit', 'TBD_00107.fit', 'TBD_00108.fit', 'TBD_00109.fit', 'TBD_00110.fit',
    'TBD_00111.fit', 'TBD_00112.fit', 'TBD_00113.fit', 'TBD_00114.fit', 'TBD_00115.fit', 'TBD_00116.fit', 'TBD_00117.fit', 'TBD_00118.fit', 'TBD_00119.fit',
    'TBD_00120.fit', 'TBD_00121.fit', 'TBD_00122.fit', 'TBD_00123.fit', 'TBD_00124.fit', 'TBD_00125.fit', 'TBD_00126.fit', 'TBD_00127.fit', 'TBD_00128.fit',
    'TBD_00129.fit', 'TBD_00130.fit', 'TBD_00131.fit', 'TBD_00132.fit', 'TBD_00133.fit', 'TBD_00134.fit', 'TBD_00135.fit', 'TBD_00136.fit', 'TBD_00137.fit',
    'TBD_00138.fit', 'TBD_00139.fit', 'TBD_00140.fit', 'TBD_00141.fit', 'TBD_00142.fit', 'TBD_00143.fit', 'TBD_00144.fit', 'TBD_00145.fit', 'TBD_00146.fit',
    'TBD_00147.fit', 'TBD_00148.fit', 'TBD_00149.fit', 'TBD_00150.fit', 'TBD_00151.fit', 'TBD_00152.fit', 'TBD_00153.fit', 'TBD_00154.fit', 'TBD_00155.fit',
    'TBD_00156.fit', 'TBD_00157.fit', 'TBD_00158.fit', 'TBD_00159.fit', 'TBD_00160.fit', 'TBD_00161.fit', 'TBD_00162.fit', 'TBD_00163.fit', 'TBD_00164.fit',
    'TBD_00165.fit', 'TBD_00166.fit', 'TBD_00167.fit', 'TBD_00168.fit', 'TBD_00169.fit', 'TBD_00170.fit', 'TBD_00171.fit', 'TBD_00172.fit', 'TBD_00173.fit',
    'TBD_00174.fit', 'TBD_00175.fit', 'TBD_00176.fit', 'TBD_00177.fit', 'TBD_00178.fit', 'TBD_00179.fit', 'TBD_00180.fit', 'TBD_00181.fit', 'TBD_00182.fit',
    'TBD_00183.fit', 'TBD_00184.fit', 'TBD_00185.fit', 'TBD_00186.fit', 'TBD_00187.fit', 'TBD_00188.fit', 'TBD_00189.fit', 'TBD_00190.fit', 'TBD_00191.fit',
    'TBD_00192.fit', 'TBD_00193.fit', 'TBD_00194.fit', 'TBD_00195.fit', 'TBD_00196.fit', 'TBD_00197.fit', 'TBD_00198.fit', 'TBD_00199.fit', 'TBD_00200.fit',
    'TBD_00201.fit', 'TBD_00202.fit', 'TBD_00203.fit', 'TBD_00204.fit', 'TBD_00205.fit', 'TBD_00206.fit', 'TBD_00207.fit', 'TBD_00208.fit', 'TBD_00209.fit',
    'TBD_00210.fit', 'TBD_00211.fit', 'TBD_00212.fit', 'TBD_00213.fit', 'TBD_00214.fit', 'TBD_00215.fit', 'TBD_00216.fit', 'TBD_00217.fit', 'TBD_00218.fit',
    'TBD_00219.fit'
],
)
def test_errors(filename):
    filestring = 'tests/ignore/'+filename
    stream = Stream.from_file(filestring)
    decoder = Decoder(stream)
    messages, errors = decoder.read()

    if len(errors) > 0:
        assert "FIT Runtime Error" in str(errors[0])



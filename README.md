# PS2-Marl-Oukoku-Monogatari

Tenshi no Present: Marl Ōkoku Monogatari

<img src="https://psxdatacenter.com/psx2/images2/covers/SLPS-20053.jpg">

-------------------------

Unpacker and packer for `DATA.DAT`<br/>

## Usage

### Extract
```shell
python data.py --mode=extract
```
Extracts `DATA.DAT` using `SECTOR.H` to directory `DATA`

Requires `DATA.DAT` and `SECTOR.H` in the same directory

-------------------------

### Create
```shell
python data.py --mode=create
```
Builds `DATA.DAT` and `SECTOR.H`

Requires directory `DATA` and file `REBUILD_LIST.txt` from the `extract` process.

-------------------------

## Extra

Built with Python 3.9.7

Created on 9/20/2022 at 11:30 AM GMT

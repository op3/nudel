#  SPDX-License-Identifier: GPL-3.0+
#
# Copyright © 2026 nudel contributors.
#
# This file is part of nudel.
#
# nudel is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# nudel is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with nudel.  If not, see <http://www.gnu.org/licenses/>.

"""Synthetic ENSDF datasets for testing.

Fictitious superheavy nucleus ``50019`` (Z=119, A=500, N=381) — no such
nuclide exists in nature. All values are invented; no real ENSDF data is
copied. The format is strictly ENSDF (column-sliced, 80-char lines) so
the real ``nudel.core`` parser is exercised against realistic record
layouts.

ENSDF encodes Z>=100 via the numeric form ``AAAZZZ`` in the 5-char nucid
field (e.g. ``50019`` → A=500, Z=119). The parent in the decay dataset is
``500OG`` (Z=118, oganesson — the last element with a symbol).
"""

from __future__ import annotations

ADOPTED_LEVELS_50019 = """\
50019    ADOPTED LEVELS, GAMMAS                                  2026SM01 202601
50019 c  Synthetic ENSDF fixture: fictitious superheavy nucleus (Z=119, A=500). 
500191c  All values are invented; no real ENSDF data is represented here.       
50019  H TYP=FUL$AUT=J. Smith$DAT=2026$                                         
50019  Q     -1500050    420030    580040    3200    60                 2026SM01
50019  XA500OG B- DECAY                                                         
50019  XB50019 EC DECAY                                                         
500  R 88SM01  J. Smith, Synth. Nucl. Data, 2026, Vol 1, p500                   
50019 PN                                                                    6   
50019  N        1.0 1     1.0 1     100 1     1.0     1    1.0 1                
50019  L        0.0  3/2-                  1.2 MS     3                         
50019  G      156.4 4     100  [E1]                    1.28E-3 2                
50019  L      156.4 45/2+                 0.82 FS     7                         
50019 cL E$First excited state, E1 transition to ground state.                  
50019  G      156.4 4     100  [M1+E2]      0.420     29.10E-413      0.42 1    
500191   BE1W=0.042 7$BM1W=0.420 7                                              
500191   G FL=0.0                                                               
50019  L      412.3 57/2-                  1.5 NS     2                       M 
50019  L      890.1 7(1/2+)                3.4 PS     6                        S
50019  L     1245.0109/2+                  12 KEV     4                        ?
50019  L   X+1850.0  11/2-                 2.1 NS     3                         
50019  L     2200.0156+                    0.5 NS     1               0.31 3    
50019  L     2680.0204+                    8.0 NS     2                         
500191   %P=100                                                                 
50019  L     3150.0254,5,6(-)               15 NS     3                         
50019  G      412.3 5      42  [E2]          0.42     1 4.2E-2 1               ?
50019  G     2680.020      21  [E1]          0.21     1 2.1E-2 1                
50019X   XREF=A                                                                 
"""

DECAY_50019_FROM_500OG = """\
50019    500OG B- DECAY                                2026SM01 202601          
50019 c  Synthetic ENSDF fixture: 50019 via beta decay from 500Og (Z=118).      
50019  H TYP=FUL$AUT=J. Smith$DAT=2026$                                         
500OG  P        0.0  0+                    1.5 MS     5               1520050   
50019 PN                                                                    3   
50019  N        1.0 1     1.0 1     100 1     1.0     1    1.0 1                
50019  XAADOPTED LEVELS, GAMMAS                                                 
50019  L        0.0  3/2-                  1.2 MS     3                         
50019  B      1520050     100 1              6.42     1                         
500191   EAV=6433.44 49                                                         
50019  L      156.4 45/2+                 0.82 FS     7                         
50019  B      1504450      42 7              6.84     1                         
50019  G      156.4 4      42  [M1]          0.42     1 4.2E-2 1                
"""

DATASETS = {
    ((500, 119), "ADOPTED LEVELS, GAMMAS"): ADOPTED_LEVELS_50019,
    ((500, 119), "500OG B- DECAY"): DECAY_50019_FROM_500OG,
}

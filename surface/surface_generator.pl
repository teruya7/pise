
if ($ARGV[0] eq "--unique_nonpolar"){
#crystallographic conventional ni suru
#cap: menseki ga saisyou slab no $cap bai wa hyouji sinai
	my $cap=9999;
	$cap=$arg2[3] if ($arg2[3] ne "");
	my @a=&get_bposcar;
	my @data;
	my ($hmax, $kmax, $lmax)=(4,4,4);
	$hmax=$arg2[0] if ($arg2[0] ne "");
	$kmax=$arg2[1] if ($arg2[1] ne "");
	$lmax=$arg2[2] if ($arg2[2] ne "");
	for (my $h=0; $h<=$hmax; $h++){
		for (my $k=-$kmax; $k<=$kmax; $k++){
			for (my $l=-$lmax; $l<=$lmax; $l++){
				push @data, ($h, $k, $l) if (&is_unique_nonpolar($a[0],$h,$k,$l));
			}
		}
	}
	die ("nonpolar suface ga nai: space group $a[0] \n") if ($data[0] eq "");
	&nonpolar_area_sort($cap,@data);
	exit;
}


=pod
Phonopy:BPOSCAR wo nyusyu, yomikomu
Kuukangun jyouhou (bangou, kigou, centering, Bravais kousi,
kakutyo Bravais kousi), tengun, phonopy version type wo kaesu
@x @y @z wo uwagaki

$_[0]="noclear": phonopy no file wo nokosu

Extended Bravais symbol: Bravais lattice + type (1-3) + inversion (Y/N)
Bravais lattice and type:
cP1: #195-206
cP2: #207-230
cF1: #195-206
cF2: #207-230
cI1
tP1
tI1:c<a
tI2:c>a
oP1
oF1:a^-2>b^-2+c^-2
oF2:c^-2>a^-2+b^-2
oF3:a^-2, b^-2, c^-2 edges of triangle
oI1:c largest
oI2:a largest
oI3:b largest
oC1:a<b
oC2:a>b
oA1:b<c
oA2:b>c
hP1:#143-149, 151, 153, 157, 159-163
hP2:Other
hR1:sqrt(3)a<sqrt(2)c
hR2:sqrt(3)a>sqrt(2)c
mP1
mC1:b<asin(beta)
mC2:b>asin(beta) BZ 12-face
mC3:b>asin(beta) BZ 14-face
aP1
=cut

sub get_bposcar{
#kyousei D
	if ($dc eq "C"){
		$dc="D";
		&c2d;
	}
#phonopy
	&writePOSCAR ("tsubo_temp_poscar");
	&run_phonopy;

#BPOSCAR wo yomu:
#Note: motono POSCAR no cartesian genshi ichi wa keisyou sarenai!
	$scale=1;
	@latvec=@x=@y=@z=@w=();
	@latvec=&split3(`head -3 BPOSCAR | tail -1`);
	@latvec=(@latvec,&split3(`head -4 BPOSCAR | tail -1`));
	@latvec=(@latvec,&split3(`head -5 BPOSCAR | tail -1`));
	my @abcreal=&get_abc(@latvec);
#BPOSCAR ha vasp 4 to 5 ryouhou sonzai
	my $vasp5check=`head -8 BPOSCAR | tail -n 1 | cut -b-1 `;
	chop $vasp5check;
	if ($vasp5check eq "D"){
		@numspecies=&splitall(`head -7 BPOSCAR | tail -1`);
		system ("tail -n +9 <BPOSCAR>tsubo_temp_poscar");
	} else {
		@numspecies=&splitall(`head -6 BPOSCAR | tail -1`);
		system ("tail -n +8 <BPOSCAR>tsubo_temp_poscar");
	}
	$num_atoms=&numatoms;
	open BPOSCAR, "tsubo_temp_poscar";
	for (my $i=0; $i<$num_atoms; $i++){
		my $t=<BPOSCAR>;
		my @b=&split4($t);
		$x[$i]=$b[0];
		$y[$i]=$b[1];
		$z[$i]=$b[2];
	}
	close BPOSCAR;
#check phonopy version
	my @line1=&splitall(`head -1 tsubo_temp_phonopyout | tail -1`);
	$line1[1] =~ s/\'//g;
	my @phonover = split(/\./, $line1[1] );
#phonopy version type
#1.11.12 ikou ha "b"
#other "a"
	my $phonotype="b";
	if (($phonover[0] <=1)&&($phonover[1] <=10)){
		$phonotype="a" ;
	} elsif (($phonover[0] ==1)&&($phonover[1] ==11)&&($phonover[2] <12)){
		$phonotype="a" ;
	}
#kuukan gun wo check
	my ($center, $spgsymbol, $spgnumber, $ptg)=(0,0,0,0);
	if ($phonotype eq "a"){
		my @b=&splitall(`head -2 tsubo_temp_phonopyout | tail -1`);
#centering
		$center=substr($b[1], 0, 1);
#kuukan gun
		$spgsymbol=$b[1];
		$spgnumber=substr($b[2], 1, -1);
#ten gun
		@b=&split3(`head -3 tsubo_temp_phonopyout | tail -1`);
		$ptg=$b[1];
	} elsif ($phonotype eq "b"){
#centering
		my @b=&splitall(`head -2 tsubo_temp_phonopyout | tail -1`);
		$b[1] =~ s/\'//g;
		$spgsymbol=$b[1];
		$center=substr($spgsymbol, 0, 1);
#kuukan gun bangou
		@b=&splitall(`head -3 tsubo_temp_phonopyout | tail -1`);
		$spgnumber=$b[1];
#ten gun
		my @b=&splitall(`head -4 tsubo_temp_phonopyout | tail -1`);
		$b[1] =~ s/\'//g;
		$ptg=$b[1];
	} 
#inversion
	my $inversion="N";
	$inversion="Y" if ($spgnumber==2);
	$inversion="Y" if (&within($spgnumber,10,15));
	$inversion="Y" if (&within($spgnumber,47,74));
	$inversion="Y" if (&within($spgnumber,83,88));
	$inversion="Y" if (&within($spgnumber,123,142));
	$inversion="Y" if (&within($spgnumber,147,148));
	$inversion="Y" if (&within($spgnumber,162,167));
	$inversion="Y" if (&within($spgnumber,175,176));
	$inversion="Y" if (&within($spgnumber,191,194));
	$inversion="Y" if (&within($spgnumber,200,206));
	$inversion="Y" if (&within($spgnumber,221,230));
#lattice type
	my $lattice_type;
	my $bravais_symbol;
	my $bravais_symbol2="X";
	my $type=1;
	if ($spgnumber <= 2){
		$lattice_type="Triclinic";
		$bravais_symbol="aP";
	} elsif ($spgnumber <= 15){
		$lattice_type="Monoclinic";
		if ($center eq "P") {
			$bravais_symbol="mP";
		} else {
			$bravais_symbol="mS";
			$bravais_symbol2="mC";
			my $t1=$abcreal[0]*&sind($abcreal[4])/$abcreal[1];
			if ($t1 < 1){
				my $t2=1+$abcreal[0]*&cosd($abcreal[4])/$abcreal[2]-$t1*$t1;
				$type=2;
				$type=3 if ($t2 < 0);
			}
		}
	} elsif ($spgnumber <= 74){
		$lattice_type="Orthorhombic";
		if ($center eq "P"){
			$bravais_symbol="oP";
		} elsif ($center eq "I") {
			$bravais_symbol="oI";
			$type=2 if (($abcreal[0]>$abcreal[1]) && ($abcreal[0]>$abcreal[2]));
			$type=3 if (($abcreal[1]>$abcreal[0]) && ($abcreal[1]>$abcreal[2]));
		} elsif ($center eq "F") {
			$bravais_symbol="oF";
			my $a2=1/$abcreal[0]/$abcreal[0];
			my $b2=1/$abcreal[1]/$abcreal[1];
			my $c2=1/$abcreal[2]/$abcreal[2];
			if ($a2>($b2+$c2)){
				$type=1;
			} elsif ($c2>($a2+$b2)){
				$type=2;
			} else {
				$type=3;
			}
		} elsif (&within($spgnumber,38,41)) {
			$bravais_symbol="oS";
			$bravais_symbol2="oA";
			$type=2 if ($abcreal[1]>$abcreal[2]);
		} else {
			$bravais_symbol="oS";
			$bravais_symbol2="oC";
			$type=2 if ($abcreal[0]>$abcreal[1]);
		}
	} elsif ($spgnumber <= 142){
		$lattice_type="Tetragonal";
		if ($center eq "P") {
			$bravais_symbol="tP";
		} else {
			$bravais_symbol="tI";
			$type=2 if ($abcreal[2]>$abcreal[0]);
		}
	} elsif ($spgnumber <= 194){
		$lattice_type="Hexagonal_Rhombohedral";
		if ($center eq "P") {
			$bravais_symbol="hP";
			$type=2;
			$type=1 if (&within($spgnumber,143,149));
			$type=1 if ($spgnumber==151);
			$type=1 if ($spgnumber==153);
			$type=1 if ($spgnumber==157);
			$type=1 if (&within($spgnumber,159,163));
		} else {
			$bravais_symbol="hR";
			my $t=sqrt(3)*$abcreal[0]/sqrt(2)/$abcreal[2];
			$type=2 if ($t>1);
		}
	} else {
		$lattice_type="Cubic";
		if ($center eq "P"){
			$bravais_symbol="cP";
			$type=2 if (&within($spgnumber,207,230));
		} elsif ($center eq "I") {
			$bravais_symbol="cI";
		} else {
			$bravais_symbol="cF";
			$type=2 if (&within($spgnumber,207,230));
		}
	}
	$bravais_symbol2=$bravais_symbol if ($bravais_symbol2 eq "X");
	my $extended_bravais_symbol=$bravais_symbol2.$type.$inversion;
	&clear_phonopy if ($_[0] ne "noclear");
	return ($spgnumber, $spgsymbol, $center, $lattice_type, $bravais_symbol, $extended_bravais_symbol, $ptg, $phonotype);
}




#unique nonpolar orientation = 1, sore igai 0
#input ($space_group_number, $h, $k, $k)
# teigi wa Phys Rev Mater 2, 124603 (2018)
sub is_unique_nonpolar{
	my $sg=$_[0];
#seisuu igai ga areba hajiku
	my $h=$_[1];
	my $k=$_[2];
	my $l=$_[3];
	die ("H $h not integer") if ($h !~ /^[+-]?\d+$/ );
	die ("K $k not integer") if ($k !~ /^[+-]?\d+$/ );
	die ("L $l not integer") if ($l !~ /^[+-]?\d+$/ );
#coprime + all non-negative igai wo hajiku 
	return (0) if (&gcmmany(@_[1..3]) != 1);
#h>0
#	return (0) if ($h < 0);
#individual
	if ($sg == 2){
		return (1) if ($h > 0);
		return (1) if (($h == 0) && ($k >= 0));
	} elsif (&within($sg,3,5)){
		return (1) if (($h >= 0) && ($k == 0));
	} elsif (&within($sg,6,9)){
		return (1) if (! &same_array(@_[1..3],0,1,0));
	} elsif (&within($sg,10,15)){
		return (1) if (($h >= 0) && ($k >= 0));
	} elsif (&within($sg,16,24)){
		return (1) if (($h >= 0) && ($k > 0) && ($l == 0));
		return (1) if (($h > 0) && ($k == 0) && ($l >= 0));
		return (1) if (($h == 0) && ($k >= 0) && ($l > 0));
	} elsif (&within($sg,25,46)){
		return (1) if (($h >= 0) && ($k >= 0) && ($l == 0));
	} elsif (&within($sg,47,74)){
		return (1) if (($h >= 0) && ($k >= 0) && ($l >= 0));
	} elsif (&within($sg,75,80)){
		return (1) if (($h >= 0) && ($k > 0) && ($l == 0));
	} elsif (&within($sg,81,82)){
		return (1) if (($h >= 0) && ($k > 0) && ($l == 0));
		return (1) if (! &same_array(@_[1..3],0,0,1));
	} elsif (&within($sg,83,88)){
		return (1) if (($h >= 0) && ($k > 0) && ($l >= 0));
		return (1) if (! &same_array(@_[1..3],0,0,1));
	} elsif (&within($sg,89,98)){
		return (1) if (($h >= $k) && ($k > 0) && ($l == 0));
		return (1) if (($h > 0) && ($k == 0) && ($l >= 0));
		return (1) if (($h >= 0) && ($k == $h) && ($l > 0));
	} elsif (&within($sg,99,110)){
		return (1) if (($h >= $k) && ($k >= 0) && ($l == 0));
	} elsif (&within($sg,111,114) || &within($sg,121,122)){
		return (1) if (($h >= $k) && ($k >= 0) && ($l == 0));
		return (1) if (($h >= 0) && ($k == 0) && ($l > 0));
	} elsif (&within($sg,115,120)){
		return (1) if (($h >= $k) && ($k >= 0) && ($l == 0));
		return (1) if (($h >= 0) && ($k == $h) && ($l > 0));
	} elsif (&within($sg,123,142)){
		return (1) if (($h >= $k) && ($k >= 0) && ($l >= 0));
	} elsif ($sg == 147){
#2019/11/13 ERROR FOUND IN PRM 2 124603
#ORIGINAL
#		return (1) if (($h >= 0) && ($k >= 0));
#NEW
#h>0,k>=0,l
#0,0,1
		if (($h == 0) && ($l == 0)){
			return (1) if ($l == 1);
			return (0);
		}
		return (1) if (($h > 0) && ($k >= 0));
	} elsif ($sg == 148){
#2019/11/13 ERROR FOUND IN PRM 2 124603
#ORIGINAL
#		my @r=&product_mv(2,1,1,-1,1,1,-1,-2,1,@_[1..3]);
#		return (1) if (($r[0] > $r[2]) && ($r[1] > $r[2]) && ($r[0] > 0) && ($r[1] > 0) && ($r[0] != $r[1]));
#		return (1) if (($r[0] > 0) && ($r[1] == $r[0]) && ($r[2] != 0));
#		return (1) if (($r[0] > 0) && ($r[2] == 0));
#NEW
#FIRST 2 OK
#h>=0,k!=0,l=0
#1,0,0
		my @r=&product_mv(2,1,1,-1,1,1,-1,-2,1,@_[1..3]);
		return (1) if (($r[0] > $r[2]) && ($r[1] > $r[2]) && ($r[0] > 0) && ($r[1] > 0) && ($r[0] != $r[1]));
		return (1) if (($r[0] > 0) && ($r[1] == $r[0]) && ($r[2] != 0));
		return (1) if (($r[0] > 0) && ($r[1] != 0) &&($r[2] == 0));
		return (1) if (($r[0] == 1) && ($r[1] == 0) &&($r[2] == 0));
	} elsif (($sg == 149) || ($sg == 151) || ($sg == 153)){
		return (1) if (($h >= 0) && ($k == $h));
	} elsif ($sg == 155){
		my @r=&product_mv(2,1,1,-1,1,1,-1,-2,1,@_[1..3]);
		return (1) if (($r[0] >= 0) && ($r[1] == $r[0]));
	} elsif (($sg == 150) || ($sg == 152) || ($sg == 154)){
		return (1) if (($h >= 0) && ($k == 0));
	} elsif (($sg == 156) || ($sg == 158)){
		return (1) if (! &same_array(@_[1..3],1,1,0));
	} elsif (($sg == 157) || ($sg == 159)){
		return (1) if (! &same_array(@_[1..3],1,0,0));
	} elsif (&within($sg,160,161)){
		my @r=&product_mv(2,1,1,-1,1,1,-1,-2,1,@_[1..3]);
		return (1) if (! &same_array(@r,1,0,-1));
	} elsif (&within($sg,162,163)){
		return (1) if (($h >= $k) && ($k > 0));
		return (1) if (($h >= 0) && ($k == 0) && ($l >= 0));
	} elsif (&within($sg,164,165)){
#2019/11/13 TYPO FOUND IN PRM 2 124603 should be -3m1
		return (1) if (($h > $k) && ($k >= 0));
		return (1) if (($h >= 0) && ($k == $h) && ($l >= 0));
	} elsif (&within($sg,166,167)){
		my @r=&product_mv(2,1,1,-1,1,1,-1,-2,1,@_[1..3]);
		return (1) if (($r[0] >= $r[1]) && ($r[1] >= $r[2]) && ($r[1] > 0) && ($r[2] != 0));
		return (1) if (($r[0] >= abs($r[1])) && (abs($r[1]) >= 0) && ($r[2] == 0));
	} elsif (&within($sg,168,173)){
		return (1) if (($h > 0) && ($k >= 0) && ($l == 0));
	} elsif ($sg == 174){
		return (1) if (! &same_array(@_[1..3],0,0,1));
	} elsif (&within($sg,175,176)){
		return (1) if (($h > 0) && ($k >= 0) && ($l >= 0));
		return (1) if (! &same_array(@_[1..3],0,0,1));
	} elsif (&within($sg,177,182)){
		return (1) if (($h >= $k) && ($k > 0) && ($l == 0));
		return (1) if (($h > 0) && ($k == 0) && ($l >= 0));
		return (1) if (($h >= 0) && ($k == $h) && ($l > 0));
	} elsif (&within($sg,183,186)){
		return (1) if (($h >= $k) && ($k >= 0) && ($l == 0));
	} elsif (&within($sg,187,188)){
		return (1) if (($h >= 0) && ($k == $h) && ($l >= 0));
	} elsif (&within($sg,189,190)){
		return (1) if (($h >= 0) && ($k == 0) && ($l >= 0));
	} elsif (&within($sg,190,194)){
		return (1) if (($h >= $k) && ($k >= 0) && ($l >= 0));
	} elsif (&within($sg,195,199)){
		return (1) if (($h >= 0) && ($k >= 0) && ($l -= 0));
	} elsif (&within($sg,200,206)){
		return (1) if (($h > $l) && ($k > $l) && ($l >= 0) && ($h != $k));
		return (1) if (($h >= 0) && ($k == $h) && ($l >= 0));
	} elsif (&within($sg,207,214)){
		return (1) if (($h >= 0) && ($k == $h) && ($l >= 0));
		return (1) if (($h > $k) && ($k > 0) && ($l == 0));
	} elsif (&within($sg,215,220)){
		return (1) if (($h >= $k) && ($k >= 0) && ($l == 0));
	} elsif (&within($sg,221,230)){
		return (1) if (($h >= $k) && ($k >= $l) && ($l >= 0));
	}
	return (0);
}



sub nonpolar_area_sort{
#Nonpolar indices (h1, k1, l1, h2, l2, k2...) wo hikisuu
#Hikisuu wa 3 no baisuu, 0 igai
#Cell ha conventional wo katei
#saisyou no $_[0] (cap) bai ijyou wa hyouji sinai
	my (@h, @k, @l, @area);
	my $count=($#_)/3;
#Empty lattice wo tsukuru
	$dc="D";
#hairetu wo yomu 
	for (my $i=0;$i<$count;$i++){
		$h[$i]=$_[3*$i+1];
		$k[$i]=$_[3*$i+2];
		$l[$i]=$_[3*$i+3];
	}
#cell wo backup
	my @x_orig=@x;
	my @y_orig=@y;
	my @z_orig=@z;
	my @w_orig=@w;
	my @latvec_orig=@latvec;
	my @numspecies_orig=@numspecies;
	my @namespecies_orig=@namespecies;

#menseki wo nyuusyu
	for (my $i=0;$i<$count;$i++){
#cell wo modosu
		@x=@x_orig;
		@y=@y_orig;
		@z=@z_orig;
		@w=@w_orig;
		@latvec=@latvec_orig;
		@numspecies=@numspecies_orig;
		@namespecies=@namespecies_orig;	
		$num_atoms=&numatoms;
		&get_hkl_cell("primitive", $h[$i], $k[$i], $l[$i]);
		$area[$i]=&norm(&cross_vv(@latvec[0..5]));
	}
#sort
	my @order_key=&order_key_number(@area);
	@h=@h[@order_key];
	@k=@k[@order_key];
	@l=@l[@order_key];
	@area=@area[@order_key];

	for (my $i=0;$i<$count;$i++){
		my $t=$area[$i]/$area[0];
		if ($t <= $_[0]){
			print ("$h[$i] $k[$i] $l[$i] ");
			printf ("%2.2f %2.2f\n", $area[$i], $area[$i]/$area[0]);
		}
	}
	exit;
}


#Cartesian to Direct
sub c2d{
	for (my $i=0; $i<$num_atoms; $i++){
		my @invlatvec=&invmatrix3(@latvec);
		($x[$i],$y[$i],$z[$i])=&product_vm($x[$i],$y[$i],$z[$i],@invlatvec);
	}
}
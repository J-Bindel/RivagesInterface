CHR=$1

for site in {1..30}
do
    python ErrorComput.py -f /run/media/jnsll/b0417344-c572-4bf5-ac10-c2021d205749/exps_modflops/results/ -approx 0 -chr $CHR -hfeats -perm 27.32 -site $site -sd 1
done

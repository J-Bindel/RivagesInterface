CHR=$1

for site in {31..40}
do
    for rate in 2 7 15 21 30 45 50 60 75 90 100 125 150 182 200 250 300 330 365 550 640 730 1000 1500 2000 2250 3000 3182 3652
    do
        python ErrorComput.py -f /run/media/jnsll/b0417344-c572-4bf5-ac10-c2021d205749/exps_modflops/results/ -approx 0 -chr $CHR -hfeats -perm 27.32 -site $site -rate $rate
    done
done

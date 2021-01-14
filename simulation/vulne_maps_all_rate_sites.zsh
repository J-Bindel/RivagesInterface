for s in 1 6 7 8 9 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25
do
    for r in 2 7 30 90 182 365 730 3652
    do
        python VulnerabilityMaps.py -f /run/media/jnsll/b0417344-c572-4bf5-ac10-c2021d205749/exps_modflops/results/ -approx 0 -chr 0 -site $s -rate $r
    done
done

#2 3 4 5 6 7 8 9 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25
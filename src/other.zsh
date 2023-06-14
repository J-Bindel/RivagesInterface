for s in 1 2 3 4 5 6 7 
do
    # for r in 2 7 30 90 182 365 730 3652
    # do
    python VulnerabilityMaps.py -f /run/media/jnsll/b0417344-c572-4bf5-ac10-c2021d205749/exps_modflops/results/ -approx 0 -chr 0 -site $s -rate 3652 -v
    # done
done

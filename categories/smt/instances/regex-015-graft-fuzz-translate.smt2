(declare-const x String)
(declare-const y String)
(assert (str.in.re x (str.to.re "[*&,")))
(assert (str.in.re y (re.* (re.* (re.+ (str.to.re "H1h;'\r'"))))))
(assert (= (str.len x) (str.to.int y)))
(assert (= 6 4))
(check-sat)
(get-model)
compile_latex:
	name='$(name)';\
	pdflatex '$(name)'.tex;\
	bibtex ${name};\
	pdflatex '$(name)'.tex;\
	pdflatex '$(name)'.tex

clean:
	rm *.aux;\
	rm *.bbl;\
	rm *.blg;\
	rm *.log;\